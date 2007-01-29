init:

    python:
        # Set up the window.
        config.screen_width = 350
        config.screen_height = 450
        config.window_title = "Ren'Py Launcher"

        # Disables sound (for the demo game).
        config.sound = False

        # Create some launcher styles.
        style.create('launcher_button', 'button')
        style.create('launcher_button_text', 'button_text')
        style.create('launcher_title_label', 'default')
        style.create('launcher_label', 'default')
        style.create('launcher_input', 'default')
        style.create('launcher_text', 'default')
        style.create('launcher_bottom_vbox', 'vbox')
        style.create('launcher_mid_vbox', 'vbox')

        style_backup = renpy.style.backup()
        
        _launcher_per_page = 8
        
        # Choose the roundrect theme for the buttons.
        theme.roundrect(launcher=True)

        def ifrw(label):
            if project.info.get("ro", False):
                return None
            else:
                return ui.jumps(label)            

        # We don't want the user going into the game menu.
        def interact():
            ui.window(background=Solid("#0008"), ypos=1.0, yminimum=80, xmargin=0, ymargin=0)
            ui.null()

            ui.image("eileen_small.png", xalign=0.0, yalign=1.0)
            ui.add(DynamicDisplayable("Text(_(store.message), size=14, color='#fff', xpos=100, ypos=375, xmaximum=240)"))
            ui.text(renpy.version(), xalign=0, yalign=1.0, size=12, color='#000')
            
            return ui.interact(suppress_underlay=True)

        def title(name):
            ui.window(style='mm_root')
            ui.null()

            ui.frame(xminimum=350, yminimum=370)
            _label_factory(name, "launcher_title", size=28)
            
            # ui.text(name, xpos=4, ypos=4, size=30, color="#559")

        def text(name, style="launcher_text"):
            ui.text(_(name), style=style)
            
        def label(name):
            _label_factory(name, "launcher")
            
        def spacer():
            ui.add(Null(1, 6))

        def mid(focus="mid"):
            ui.vbox(style='launcher_mid_vbox', focus=focus)

        def bottom(focus="bottom"):
            ui.vbox(style='launcher_bottom_vbox', focus=focus)

        def button(text, hover_text=None, clicked=None, hovered=None):
            if hover_text:
                def hovered(hover_text=hover_text):
                    if store.message != hover_text:
                        store.message = hover_text
                        renpy.restart_interaction()
                        
            # ui.button(clicked=clicked, hovered=hovered)
            # ui.text(text, style="button_text")
            _button_factory(text, 'launcher', clicked=clicked, hovered=hovered)
                

        def prompt(name, message, cancel, default='', hint=''):
            store.message = hint

            # Creating the project.
            title(name)

            mid()

            text(message)

            ui.input(default, exclude='{}/\\', style='launcher_input')

            ui.close()

            bottom()
            button("Cancel", clicked=ui.jumps("main"))
            ui.close()

            return interact()

        def error(name, message, target):
            store.message = ''

            # Creating the project.
            title(name)

            mid()
            text(message)
            ui.close()

            bottom()
            button("Cancel", clicked=ui.jumps(target))
            ui.close()

            return interact()


        def paged_menu(tit, choices, message, per_page=None, cancel='main'):

            if per_page is None:
                per_page = _launcher_per_page
            
            page = 0
            pages = len(choices) / per_page


            while True:

                store.message = message

                title(tit)

                mid(focus="paged_menu")

                for name, desc, ret, hovered in choices[page * per_page:(page + 1) * per_page]:
                    button(name, desc, clicked=ui.returns(("return", ret)), hovered=hovered)
                    
                ui.close()

                bottom()

                if pages >= 1:

                    if page < pages:
                        button("Next Page", "Go to the next page of projects.", clicked=ui.returns(("page", page + 1)))
                    else:
                        button("Next Page")

                    if page > 0:
                        button("Previous Page", "Go to the previous page of projects.", clicked=ui.returns(("page", page - 1)))
                    else:
                        button("Previous Page")

                button("Cancel", "Return to the top menu.", ui.jumps(cancel))
                        
                ui.close()

                cmd, arg = interact()

                if cmd == "repeat":
                    continue
                
                if cmd == "page":
                    page = arg
                    continue

                if cmd == "return":
                    return arg

        class ProcessBehavior(renpy.display.layout.Null):

            def __init__(self, proc):
                super(ProcessBehavior, self).__init__()

                self.proc = proc

            def event(self, ev, x, y, st):

                if self.proc.poll() is not None:
                    return True

                renpy.game.interface.timeout(.25)

        class Project(object):
            def __init__(self, name, path, gamedir, info):
                # name
                self.name = name

                # path to project
                self.path = path

                # gamedir
                self.gamedir = gamedir

                self.info = info

                import re

                def upper(m):
                    return m.group(0).upper()

                title = re.sub(r'^.', upper, name)
                title = re.sub(r'\s+\S', upper, title)
                self.title = title


        def load_project(dir, name):
            import os.path

            # Ignore unicode files.
            for i in name:
                if ord(i) >= 127:
                    return 

            if os.path.isdir(dir + "/game"):
                gamedir = dir + "/game"
            elif os.path.isdir(dir + "/data"):
                gamedir = dir + "/data"
            else:
                return

            desc = u""

            info = dict()
            info["description"] = desc
            info["ignored"] = ignored
            
            if os.path.exists(dir + "/launcherinfo.py"):
                source = file(dir + "/launcherinfo.py", "rU").read().decode("utf8")
                if source[0] == u'\ufeff':
                    source = source[1:]
                source = source.encode("raw_unicode_escape")

                exec source in info

            store.projects.append(Project(name, dir, gamedir, info))
                
        def load_projects():

            import os
            import os.path

            store.projects = [ ]
            
            cwd = os.getcwd()

            if cwd == config.renpy_base:
                dirs = [ cwd ]
            else:
                dirs = [ config.renpy_base, cwd ]

            for d in dirs:

                contents = os.listdir(d)
                contents.sort()

                for dd in contents:
                    dir = d + "/" + dd

                    if os.path.isdir(dir):
                        load_project(dir, dd)

                        
            if not store.projects:
                raise Exception("The launcher will not function without any projects.")

        def lint():
            
            import renpy.subprocess as subprocess
            import sys
            import os.path

            store.message = "Lint in progress."
            title("Lint")
            ui.pausebehavior(0)
            interact()

            lf = file("lint.txt", "w+")
            
            if hasattr(sys, "winver") and sys.argv[0].lower().endswith(".exe"):
                proc = subprocess.Popen([config.renpy_base + "/console.exe", "--lint", project.path], stdin=lf, stdout=lf, stderr=lf)
            else:
                proc = subprocess.Popen([sys.executable, sys.argv[0], "--lint", project.path], stdout=lf)

            proc.wait()

            lf.close()

            renpy.launch_editor([ "lint.txt" ])


label main_menu:
    return

label find_project:

    python hide:
        load_projects()

        wanted = persistent.project or "demo"

        for p in projects:
            if p.name == wanted:
                store.project = p
                break
        else:
            store.project = projects[0]


        store.game_proc = None

    return
        
    
label start:

    call find_project from _call_find_project_1
    
label main:

    python:
        store.message = "What do you want to do?"

label top_menu:
    

    python hide:

        while True:

            title(project.title)

            mid()

            label("This Project")

            if not game_proc or game_proc.poll() is not None:
                clicked = ui.jumps("launch")
            else:
                clicked = None

            button("Launch",
                   "Starts the project running.",
                   clicked=clicked)


            if config.editor:
                button("Edit Script",
                       "Edits the script files.",
                       clicked=ui.jumps("edit"))


            button("Change Theme",
                   "Changes the color theme of the project.",
                   ifrw("choose_theme"))
                
            button("Game Directory",
                   "Opens the game directory.",
                   clicked=ui.jumps("game_directory"))



            button("Tools",
                   "Shows the tools menu.",
                   clicked=ui.jumps("tools"))

            spacer()

            label("Change Project")

            button("Select Project",
                   "Select a project to work with.",
                   clicked=ui.jumps("select_project"))

            button("New Project",
                   "Create a new project from a template.",
                   clicked=ui.jumps("new"))

            ui.close()

            bottom()
            button("Quit", "Quit the Ren'Py Launcher.", clicked=ui.jumps("confirm_quit"))
            ui.close()


            if game_proc and game_proc.poll() is None:
                ui.add(ProcessBehavior(game_proc))

            interact()

    jump top_menu

label select_project:

    python hide:

        choices = [ (p.name, p.info["description"], p, None) for p in projects ]

        store.project = paged_menu("Select a Project", choices, "Please select a project.")

        persistent.project = store.project.name

        store.game_proc = None

    jump main

label launch:

    python hide:
        import renpy.subprocess
        import sys
        import os.path

        if hasattr(sys, "winver") and sys.argv[0].lower().endswith(".exe"):
            proc = renpy.subprocess.Popen([sys.argv[0], project.path])
        else:
            proc = renpy.subprocess.Popen([sys.executable, sys.argv[0], project.path])

        store.message = project.title + " has been launched."

        store.game_proc = proc
        

    jump top_menu

            
            
label edit:

    python hide:
        import os

        
        files = [ project.gamedir + "/" + i for i in os.listdir(project.gamedir) if i.endswith(".rpy") if not i[0] == "."]

        files.sort()

        if "options.rpy" in files:
            files.remove("options.rpy")
            files.insert(0, "options.rpy")

        if "script.rpy" in files:
            files.remove("script.rpy")
            files.insert(0, "script.rpy")

        renpy.launch_editor(files)
        
        store.message = "Launched editor with %d script files." % len(files)

    jump top_menu

label game_directory:

    python hide:
        import os
        import os.path
        import platform

        gamedir = os.path.normpath(project.gamedir)

        store.message = "Opening game directory:\n%s" % gamedir

        if platform.win32_ver()[0]:
            os.startfile(gamedir)
        elif platform.mac_ver()[0]:
            import renpy.subprocess as subprocess
            subprocess.Popen([ "open", gamedir ])
        else:
            store.message = "Opening the game directory is not supported on this platform.\n%s" % gamedir

    jump top_menu
                     

label tools:

    $ store.message = "Please choose a tool you want to use with this project."

label tools_menu:

    python hide:

        title("Tools: " + project.title)

        mid()

        label("Anytime")

        button("Check Script (Lint)",
               "Checks the game's script for likely errors. This should be run before releasing.",
               clicked=ui.jumps("lint"))

        button("Quick Backup",
               "Makes a backup copy of the project. You also need to make backups somewhere other then this computer.",
               clicked=ui.jumps("backup"))

        spacer()

        label("Release Day")


        button("Add From to Calls",
               "Adds a from clause to each of the call statements in your script.", 
               clicked=ifrw("add_from_to_calls"))
        
        button("Archive Files",
               "Archive files found under the game and archived directories.",
               clicked=ifrw("archive_files"))
               
        button("Build Distributions",
               "Build distributions for the platforms supported by Ren'Py.",
               clicked=ui.jumps("distribute"))

        ui.close()

        bottom()

        button("Back",
               "Goes back to the top menu.",
               clicked=ui.jumps("main"))

        ui.close()

        interact()
        
label lint:

    python hide:
        lint()

        store.message = "A lint report should appear shortly."

    jump tools_menu
        


label archive_files:

    python hide:
        import os
        import os.path

        import renpy.tools.archiver as archiver

        extensions = persistent.extensions or "png gif jpg"
        extensions = prompt("Archiving Files", "Please enter a space separated list of the file extensions you want archived.", "tools", extensions)
        if not extensions.strip():
            renpy.jumps("tools_menu")
        persistent.extensions = extensions    
        extensions = [ i.strip() for i in extensions.strip().split() ]
        

        # Tell the user we're archiving images.
        title("Archiving Files")
        store.message = "Please wait while we archive files."
        ui.pausebehavior(0)
        interact()


        gamedir = project.gamedir
        archived = project.path + "/archived"

        files = [ ]
        prefix = gamedir + "/data"

        def should_archive(fn, extensions=extensions):
            fn = fn.lower()

            if fn[0] == ".":
                return False

            for e in extensions:
                if fn.endswith(e):
                    return True

            return False

        for bdir in gamedir, archived:

            for dirname, dirs, filenames in os.walk(bdir):

                # Ignore svn.
                dirs[:] = [ i for i in dirs if not i[0] == '.' ]

                for fn in filenames:
                    
                    fullfn = dirname + "/" + fn
                    shortfn = fullfn[len(bdir)+1:]

                    if not should_archive(shortfn):
                        continue

                    files.append((fullfn, shortfn))

        archiver.archive(prefix, files)

#         f = file(gamedir + "/images.rpy", "w")
#         print >>f, "init:"
#         print >>f, "    $ config.archives.append('images')"
#         f.close()
                    
        for fullfn, shortfn in files:
            afn = archived + "/" + shortfn

            if fullfn == afn:
                continue

            try:
                os.makedirs(os.path.dirname(afn))
            except:
                pass

            os.rename(fullfn, afn)

        store.message = "The files have been added to the archive, and moved into the archived directory."

    jump tools_menu

label backup:

    python hide:
        import os
        import time
        import shutil

        # Tell the user we're archiving images.
        title("Making Backup")
        store.message = "Please wait while we make a backup."
        ui.pausebehavior(0)
        interact()

        try:
            os.mkdir('backups')
        except:
            pass

        while True:

            btime = str(int(time.time()))
            bdir = "backups/%s.%s" % (project.name, btime)

            if not os.path.exists(bdir):
                break

            time.sleep(1)

        shutil.copytree(project.path, bdir)

        store.message = "The backup was placed into %s." % bdir

    jump tools_menu
                

label add_from_to_calls:

    python hide:
        import os
        import time
        import shutil

        title("Add From to Calls")
        store.message = "Please wait while we add from clauses to call statements."
        ui.pausebehavior(0)
        interact()

        import renpy.tools.add_from as add_from

        add_from.add_from(project.gamedir, config.commondir)

        store.message = "Done adding from clauses to call statements. You may want to remove the .bak files created."

    jump tools_menu
                
    
    
        
        
label confirm_quit:
    $ renpy.quit()
    
