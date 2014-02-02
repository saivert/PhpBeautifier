import re
import os
import subprocess

import sublime
import sublime_plugin


class PhpBeautifierCommand(sublime_plugin.TextCommand):
    def run(self, edit):        
        # Load settings
        settings = sublime.load_settings('PhpBeautifier.sublime-settings') 
        # Test environment
        if self.view.is_scratch():
            return

        if self.view.is_dirty():
            return self.status("Please save the file.")

        # check if file exists.
        FILE = self.view.file_name()
        if not FILE or not os.path.exists(FILE):
            return self.status("File {0} does not exist.".format(FILE))

        # check if extension is allowed.
        fileName, fileExtension = os.path.splitext(FILE)        
        if fileExtension[1:] not in settings.get('extensions'):
            return self.status("File {0}{1} does not have a valid extension. Please edit your settings to allow this extension.".format(fileName, fileExtension))

        # Start doing stuff
        cmd = "php_beautifier"

        # Load indent and filters settings        
        indent = settings.get('indent');
        filters = ' '.join(settings.get('filters'));
        
        allFile = sublime.Region(0, self.view.size())
        AllFileText = self.view.substr(allFile).encode('utf-8')

        if os.name == 'nt':
            cmd_win = cmd + ".bat"
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            p = subprocess.Popen([cmd_win, indent, "-l", filters, "-f", "-", "-o", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        else:
            p = subprocess.Popen([cmd, indent, "-l", filters, "-f", "-", "-o", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(AllFileText)
        if len(stderr) == 0:
            self.view.replace(edit, allFile, self.fixup(stdout))
        else:
            self.show_error_panel(self.fixup(stderr))

    # Error panel & fixup from external command
    # https://github.com/technocoreai/SublimeExternalCommand
    def show_error_panel(self, stderr):
        panel = self.view.window().get_output_panel("php_beautifier_errors")
        panel.set_read_only(False)
        edit = panel.begin_edit()
        panel.erase(edit, sublime.Region(0, panel.size()))
        panel.insert(edit, panel.size(), stderr)
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.php_beautifier_errors"})
        panel.end_edit(edit)

    def fixup(self, string):
        return re.sub(r'\r\n|\r', '\n', string.decode('utf-8'))

    def status(self, string):
        return sublime.status_message(string)