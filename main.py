from functools import partial
import multiprocessing
from flask import Flask, render_template, request, jsonify
from string_permutations import string_permutations, MaxPermutationsException
from multiprocessing import Process, Queue
import queue
import os
import atexit
from signal import signal, SIGINT
from sys import exit
from unary import unary

from uuid import uuid4, UUID
app = Flask(__name__)

PAGE_SIZE = 500
MAX_PAGES = 1000000
PROCESS_CLOSE_TIMEOUT = 5
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

_generator_queue_processes = []
def with_generator_queue(fn, *args):
    global _generator_queue_processes
    def generator_queue(q, errQ, *args):
        try:
            for i in fn(*args):
                q.put(i)
        except Exception as e:
            errQ.put(e)
    q = Queue(maxsize=PAGE_SIZE * MAX_PAGES)
    errQ = Queue()
    proc = Process(target=generator_queue, name=fn.__name__, args=(q, errQ, *args))
    proc.q = q
    proc.errQ = errQ
    proc.start()
    _generator_queue_processes.append(proc)
    print(_generator_queue_processes)
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
                proc.q.close()
                proc.errQ.close()
                proc.kill()
                proc.join()
                raise err
        if(item):
            yield item
    print('closing')

    proc.q.close()
    proc.errQ.close()
    proc.kill()
    proc.join()
        

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


def cleanup(processes):
    if(len(processes)):
        print(f"closing {len(processes)} processes")
        for p in processes:  # list of your processes
            if p.q : p.q.close()
            if p.errQ : p.errQ.close()
            p.kill()
            p.join()
            print(f"closed process {p.pid}")
        exit(0)


atexit.register(cleanup, _generator_queue_processes)

if __name__ == '__main__':
    signal(SIGINT, partial(unary(cleanup), _generator_queue_processes))
    app.run('127.0.0.1', port=os.getenv('PORT') or 8000, debug=True)

        
