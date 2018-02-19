loggers :
    root :
        level : DEBUG
        handlers : [gmHandler, consoleHandler]
handlers :
    gmHandler :
        class : classes.GMailHandler
        level : DEBUG
        formatter : gmFormatter
    consoleHandler :
        class : logging.FileHandler
        level : DEBUG
        formatter : simpleFormatter
        filename : errors.log
formatters :
    gmFormatter :
        format : "%(name)s called: Problem with %(funcName)s function in %(filename)s"
        datefmt : '%d/%m/%Y %H:%M:%S'
    simpleFormatter :
        format : "File: %(pathname)s\n%(asctime)s Failed: Line %(lineno)d in %(filename)s\nError: %(message)s\n"
        datefmt : '%d/%m/%Y %H:%M:%S'
