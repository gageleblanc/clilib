import logging

class Util:
  @staticmethod
  def dump_module(args, module):
    if args.debug:
      print(dir(module))

  @staticmethod
  def import_test():
    print("Import success!")

  @staticmethod
  def configure_logging(args, name):
    logFormatter = logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)8s] - %(message)s')
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    if args.debug:
      log.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logFormatter)
    if args.debug:
      consoleHandler.setLevel(logging.DEBUG)

    log.addHandler(consoleHandler)

    return log
