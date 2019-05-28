import os
import sys

if __name__ == '__main__':
    this_dir = os.path.abspath(os.path.dirname(__file__))
    src_dir = os.path.abspath(os.path.join(this_dir, "../backend/src"))

    # adding `src` path to PYTHONPATH
    sys.path.append(src_dir)

    try:
        from common.entities import ScheduleCategory, ScheduleQueue
    except ImportError as exp:
        print("Unable to import entities. Path issue? -- {}".format(exp))
        import traceback
        print(traceback.format_exc(exp))
        sys.exit(1)

    output = """
// please occasionaly sync this with backend via `gen_entities-ts.py script`
export let queues = {queues};
export let categories = {categories};

""".format(queues=repr(ScheduleQueue.all()),
           categories=repr(ScheduleCategory.all()),
           )

    with open(os.path.join(this_dir, "src/app/services/entities.ts"), "w") as fp:
        fp.write(output)
