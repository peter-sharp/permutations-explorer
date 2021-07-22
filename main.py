from typing import Generator
from flask import Flask, render_template, request, abort, jsonify
from string_permutations import string_permutations, MaxPermutationsException
from multiprocessing import Process, Queue
import queue
import os
import atexit
import time

from uuid import uuid4, UUID
app = Flask(__name__)

PAGE_SIZE = 500
MAX_PAGES = 1000000
generators = {}
@app.route('/', methods=['POST', 'GET'])
def index():
    word = 'test'
    err = None
    continueUuid = None
    variations = []
    if request.method == 'POST':
        word = request.form['word']

    try:
        variations = list(string_permutations(PAGE_SIZE, word))
    except MaxPermutationsException:
       
        continueUuid = uuid4()
        try:
            generator = with_generator_queue(
                string_permutations, PAGE_SIZE * MAX_PAGES, word)
            generators[continueUuid] = generator
            print(generators)
            i = 0
            for variation in generator:
                if(i >= PAGE_SIZE): break
                variations.append(variation)
                i += 1
        except MaxPermutationsException as e:
            err = str(e)
    except Exception as e:
        err = str(e)

    return render_template('index.html', variations = variations, word = word, error = err, permutationCount = len(variations), continueUuid = continueUuid)


def with_generator_queue(fn, *args):
    def generator_queue(q, errQ, *args):
        try:
            for i in fn(*args):
                q.put(i)
        except Exception as e:
            errQ.put(e)
    q = Queue(maxsize=PAGE_SIZE * MAX_PAGES)
    errQ = Queue()
    proc = Process(target=generator_queue, name=fn.__name__, args=(q, errQ, *args))
    with_generator_queue.processes.append(proc)
    proc.start()
    while proc.is_alive():
        item = None
        try:
            item = q.get(False, timeout=2)
        except queue.Empty:
            err = None
            try:
                err = errQ.get(False, timeout=2)
            except queue.Empty:
                pass
            if err:
                proc.close()
                raise err
        if(item):
            yield item
    print('closing')
    proc.close()
with_generator_queue.processes = []
        

class InvalidAPIUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidAPIUsage)
def resource_not_found(e):
    return jsonify(e.to_dict()), e.status_code

@app.route('/permutations/<id>')
def permutations(id):
    generator = generators.get(UUID(id))
    res = None
    if(generator):
        variations = []
        i = 0
        for variation in generator:
            if(i >= PAGE_SIZE):
                break
            variations.append(variation)
            i +=1
        res = variations
    else:
        raise InvalidAPIUsage("Continue not found!", status_code=404)
    return jsonify(res)


def cleanup():
    generators.clear()
    timeout_sec = 5
    for p in with_generator_queue.processes:  # list of your processes
        p_sec = 0
        for second in range(timeout_sec):
            if p.poll() == None:
                time.sleep(1)
                p_sec += 1
            if p_sec >= timeout_sec:
                p.kill()  # supported from python 2.6
    print('cleaned up!')

atexit.register(cleanup)

if __name__ == '__main__':

    app.run('127.0.0.1', port=os.getenv('PORT') or 8000, debug=True)

        
