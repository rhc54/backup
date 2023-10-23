#!/usr/bin/env python3

import os, os.path, sys, shutil, signal, glob
import logging, logging.handlers
from optparse import OptionParser, OptionGroup


def signal_handler(signal, frame):
    print("Ctrl-C received")
    sys.exit(0)

def backupDir(p:dict):
    sourcepath = p["source"]
    comppath = p["target"]
    destpath = p["dest"]

    msg = "Processing " + sourcepath
    p["log"].debug(msg)

    try:
        dirlist = os.listdir(sourcepath)
    except:
        # can't access this directory - let the person know and leave
        msg = "Source directory " + sourcepath + " could not be accessed"
        p["log"].error(msg)
        return

    for d in dirlist:
        source = os.path.join(sourcepath, d)
        msg = "Working " + source
        p["log"].debug(msg)

        if '~' == d[0]:
            pass

        elif (os.path.isdir(source)):
            # check if this directory is on the exclude list
            doprocess = True
            if "exclude" in p:
                for e in p["exclude"]:
                    if e == source:
                        doprocess = False
                        break
            if doprocess:
                newP = p
                newP["source"] = source
                newP["target"] = os.path.join(comppath, d)
                newP["dest"] = os.path.join(destpath, d)
                backupDir(newP)
            else:
                msg = "Skipping " + source
                p["log"].info(msg)

        elif '.' == d[0]:
            msg = "Ignoring " + d
            p["log"].debug(msg)
            pass

        else:
            # this is a file - see if it is on the exclude list
            doprocess = True
            if "exclude" in p:
                for e in p["exclude"]:
                    if e == source:
                        doprocess = False
                        break
                    # does this exclude have a wildcard?
                    if '*' in e:
                        elen = len(e)
                        dlen = len(d)
                        # if the wildcard is at the front, then check just the end
                        if e[0] == '*':
                            match = True
                            for n in range(elen-1):
                                if n > dlen:
                                    match = False
                                    break
                                if e[elen-n-1] != d[dlen-n-1]:
                                    match = False
                                    break
                            if match:
                                doprocess = False
                                break
                        # if wildcard is at the end, check the front
                        elif e[elen-1] == '*':
                            match = True
                            for n in range(elen-1):
                                if n > dlen:
                                    match = False
                                    break
                                if e[n] != d[n]:
                                    match = False
                                    break
                            if match:
                                doprocess = False
                                break
            if not doprocess:
                msg = "Source " + source + " is excluded - ignoring"
                p["log"].info(msg)
                continue

            # if we were given explicit include directions, check
            # to see if this one fits


            # we want to consider this file
            comp = os.path.join(comppath, d)
            dest = os.path.join(destpath, d)
            msg = "Comparing " + comp + " to " + source
            p["log"].debug(msg)

            if (os.path.exists(comp)):
                # the comparison file exists
                if "noupdate" in p and p["noupdate"]:
                    msg = "Target " + " exists but NOUPDATE is set - ignoring"
                    p["log"].debug(msg)
                    continue

                # is it different?
                modtime = os.path.getmtime(source)
                backuptime = os.path.getmtime(comp)
                msg = "Source: " + source + " Modtime: " + "{:.2f}".format(modtime) + " Comptime: " + "{:.2f}".format(backuptime)
                p["log"].debug(msg)
                if modtime < backuptime:
                    msg = "Target " + comp + " is newer - ignoring"
                    p["log"].debug(msg)
                    continue
                if modtime == backuptime:
                    msg = "Target and source are of same age - ignoring"
                    p["log"].debug(msg)
                    continue

                msg = "Source: " + source + " is newer - updating"
                try:
                    if "dryrun" in p and p["dryrun"]:
                        p["log"].info(msg)
                    else:
                        p["log"].debug(msg)
                        shutil.copy2(source, dest)
                # If source and destination are same
                except shutil.SameFileError:
                    msg = "Source and destination represents the same file: " + source
                    p["log"].error(msg)
                    pass

                # If there is any permission issue
                except PermissionError:
                    msg = "Permission denied for: " + source + " to " + dest
                    p["log"].error(msg)
                    pass

                except (IOError, OSError) as err:
                    msg = "Error backing up: " + source + " Error: " + err
                    p["log"].error(msg)
                    pass

                except:
                    msg = "Unrecognized error: " + source + " Error: " + err
                    p["log"].error(msg)
                    pass

            else:
                msg = "Target: " + comp + " does not exist"
                p["log"].debug(msg)

                if dest != comp:
                    # check the dest to see if the file there already exists
                    if (os.path.exists(dest)):
                        # is the source newer?
                        modtime = os.path.getmtime(source)
                        backuptime = os.path.getmtime(dest)
                        msg = "Source: " + source + " Modtime: " + "{:.2f}".format(modtime) + " Desttime: " + "{:.2f}".format(backuptime)
                        p["log"].debug(msg)
                        if modtime < backuptime:
                            msg = "Destination " + comp + " is newer - ignoring"
                            p["log"].debug(msg)
                            continue
                        if modtime == backuptime:
                            msg = "Destination and source are of same age - ignoring"
                            p["log"].debug(msg)
                            continue

                if "noallext" in p and p["noallext"]:
                    # check to see if only the extension differs
                    # between source and comparison
                    baseComp = os.path.splitext(comp)[0]
                    newComp = baseComp + ".*"
                    if glob.glob(newComp):
                        # ignore the file
                        msg = "Found matching file with different extension: " + source
                        p["log"].info(msg)
                        continue

                try:
                    msg = "Making dest path: " + destpath
                    if "dryrun" in p and p["dryrun"]:
                        p["log"].info(msg)
                    else:
                        p["log"].debug(msg)
                        os.makedirs(destpath)
                except OSError:
                    # directory already exists
                    pass

                try:
                    msg = "Backing up: " + source + " to " + dest
                    if "dryrun" in p and p["dryrun"]:
                        p["log"].info(msg)
                    else:
                        p["log"].debug(msg)
                        shutil.copy2(source, dest)
                # If source and destination are same
                except shutil.SameFileError:
                    msg = "Source and destination represents the same file: " + source
                    p["log"].error(msg)
                    pass

                # If there is any permission issue
                except PermissionError:
                    msg = "Permission denied for: " + source + " to " + dest
                    p["log"].error(msg)
                    pass

                except (IOError, OSError) as err:
                    msg = "Error backing up: " + source + " Error: " + err
                    p["log"].error(msg)
                    pass

                except:
                    msg = "Unrecognized error: " + source
                    p["log"].error(msg)
                    pass


def process_option(config, opt):
    tst = opt.lower()
    if "=" in tst:
        cmd,tgt = tst.split('=')
        cmd = cmd.strip()
        tgt = tgt.strip()
        if cmd == "noupdate":
            if tgt == "true":
                config["noupdate"] = True
            return True
        if cmd == "allext":
            if tgt == "false":
                config["allext"] = False
            return True
        if cmd == "exclude":
            if not config["exclude"]:
                config["exclude"] = tgt.split(',')
            else:
                config["exclude"] += tgt.split(',')
            return True
        if cmd == "log":
            config["logFile"] = tgt
            return True
    else:
        if tst == "dryrun":
            config["dryrun"] = True
            return True
        if tst == "debug":
            config["debug"] = True
            return True
        if tst == "noupdate":
            config["noupdate"] = True
            return True
        if tst == "noallext":
            config["allext"] = False
            return True

    # must not be a recognized option
    print("unrecognized option", opt)
    return False

def validate(config):
    # must give us a source directory
    if not "source" in config:
        print("You must provide a SOURCE directory")
        return False
    # see if the source directory exists
    if not os.path.exists(config["source"]):
        print("SOURCE directory",config["source"],"does not exist")
        return False
    # must give us a DESTINATION directory
    if not "dest" in config:
        print("You must provide a DESTINATION directory")
        return False
    # see if the destination directory exists
    if not os.path.exists(config["dest"]):
        if "dryrun" in config and config["dryrun"]:
            pass
        else:
            # try to create the path
            os.makedirs(config["dest"], 0o777)
            # check to see if it was created
            if not os.path.exists(config["dest"]):
                print("ERROR: DESTINATION path", config["dest"], "could not be created")
                return False
    # if they didn't give us a TARGET directory, default
    # it to the DESTINATION
    if not "target" in config:
        config["target"] = config["dest"]
    # if we have a logFile, then setup the logger for it
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    if "logFile" in config:
        config["log"] = logging.getLogger("")
        fileHandler = logging.FileHandler(config["logFile"])
        fileHandler.setFormatter(logFormatter)
        config["log"].addHandler(fileHandler)
        if "debug" in config and config["debug"]:
            config["log"].setLevel(logging.DEBUG)
        else:
            config["log"].setLevel(logging.INFO)
    elif "debug" in config and config["debug"]:
        config["log"] = logging.getLogger("")
        fileHandler = logging.StreamHandler(sys.stdout)
        fileHandler.setFormatter(logFormatter)
        config["log"].addHandler(fileHandler)
        config["log"].setLevel(logging.DEBUG)
    else:
        config["log"] = logging.getLogger("")
        fileHandler = logging.StreamHandler(sys.stdout)
        fileHandler.setFormatter(logFormatter)
        config["log"].addHandler(fileHandler)
        config["log"].setLevel(logging.WARN)

    return True

def main():

    signal.signal(signal.SIGINT, signal_handler)

    parser = OptionParser("usage: %prog [options]")
    debugGroup = OptionGroup(parser, "Debug Options")
    debugGroup.add_option("--debug",
                          action="store_true", dest="debug", default=False,
                          help="Output lots of debug messages while processing")
    debugGroup.add_option("--dryrun",
                          action="store_true", dest="dryrun", default=False,
                          help="Show commands, but do not execute them")
    debugGroup.add_option("--log", dest="log",
                         help="File in which the processing log shall be stored")
    parser.add_option_group(debugGroup)

    execGroup = OptionGroup(parser, "Execution Options")
    execGroup.add_option("--title", dest="title",
                         help="The title for this backup configuration")
    execGroup.add_option("--src", dest="src",
                         help="The head of the source directory tree")
    execGroup.add_option("--tgt", dest="tgt",
                         help="The head of the directory tree to be compared with the source (defaults to destination directory)")
    execGroup.add_option("--dest", dest="dest",
                         help="The destination directory where the files that are different are to be stored")
    execGroup.add_option("--exclude", dest="exclude",
                         help="Comma-delimited list of files and/or directories to be ignored (can include *.ext)")
    execGroup.add_option("--include", dest="include",
                         help="Comma-delimited list of files and/or directories to be included (can include *.ext)")
    execGroup.add_option("--config", dest="config",
                         help="Comma-delimited list of files containing src/tgt/dest information")
    execGroup.add_option("--noupdate",
                         action="store_true", dest="noupdate", default=False,
                         help="Do not update existing files")
    execGroup.add_option("--noallext",
                         action="store_false", dest="allext", default=True,
                         help="Do not backup files of same name but with different extensions")
    parser.add_option_group(execGroup)

    (options, args) = parser.parse_args()

    # setup the list of things to process
    process = []

    if options.src or options.dest:
        # quick check of input
        if options.src and not options.dest:
            print("If you provide a source directory, you must also provide a destination directory")
            sys.exit(1)
        if options.dest and not options.src:
            print("If you provide a destination directory, you must also provide a source directory")
            sys.exit(1)
        if options.config:
            print("Cannot provide both a config file AND specific src or dest options on the cmd line")
            sys.exit(1)
        if options.include and options.exclude:
            print("Cannot provide both include AND exclude options")
            sys.exit(1)
        # assemble the request
        config = {}
        if options.title:
            config["title"] = options.title
        config["source"] = options.src
        config["dest"] = options.dest
        if options.tgt:
            config["target"] = options.tgt
        # check the options
        if options.debug:
            config["debug"] = True
        if options.dryrun:
            config["dryrun"] = True
        if options.log:
            config["logFile"] = options.log
        if options.noupdate:
            config["noupdate"] = True
        if not options.allext:
            config["allext"] = False
        if options.exclude:
            config["exclude"] = options.exclude.split(',')
        if options.include:
            config["include"] = options.include.split(',')
        # validate the input
        if not validate(config):
            sys.exit(1)
        # add to the list
        process.append(config)
    else:
        files = options.config.split(',')
        for f in files:
            try:
                configFile = open(f, "r")
            except:
                print("File ", f, " could not be opened")
                continue


            # read all the lines in the configuration file
            input_lines = configFile.readlines()
            configFile.close()

            # cycle thru the lines and remove all those that start with '#'
            config = {}
            doprocess = True
            for l in input_lines:
                inputdata = l.strip();  # remove any white space at front or back
                if 0 < len(inputdata) and inputdata[0] == '#':
                    continue
                # if the line is empty, then we save
                # the current config dict and start
                # a new one
                if 0 == len(inputdata):
                    if bool(config):
                        if doprocess:
                            doprocess = validate(config):
                        if doprocess:
                            process.append(config)
                        else:
                            print("Config file", f, "contained an error - not processing")
                        config = {}
                        doprocess = True
                    continue
                # convert any tabs to spaces
                expinput = inputdata.expandtabs()
                if options.debug:
                    print("expanded input", expinput)
                # extract the cmd before the colon
                cmd, tgt = expinput.split(':')
                tgt = tgt.strip()
                if options.debug:
                    print("command", cmd)
                # add to the current dictionary
                if cmd.lower() == "option":
                    doprocess = process_option(config, tgt)
                elif cmd.lower() == "exclude":
                    tmp = tgt.split(',')
                    if not "exclude" in config:
                        config["exclude"] = tmp
                    else:
                        config["exclude"] += tmp
                else:
                    config[cmd.lower()] = tgt
            if bool(config):
                if doprocess:
                    doprocess = validate(config)
                if doprocess:
                    process.append(config)
                else:
                    print("Config file", f, "contained an error - not processing")

    for p in process:
        if "title" in p:
            if "log" in p:
                tmp = "Processing: " + p["title"]
                p["log"].debug(tmp)
            else:
                print("Processing:", p["title"])
        print(p)
        backupDir(p)

if __name__ == '__main__':
    main()
