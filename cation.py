import json
import pprint
import sys
import time

class Cation:
    def init_todo_repo (self):
        self.data = {
            'cation': True,        # signature
            'count': 0,            # number of items
            'a': {},               # items
        }

    def init_item (self, content, state='todo'):
        return {
            'c': content,
            's': state,
            # Other: links labelled by number
            # 'P': parent <- using simple links for now
        }

    def get_parent (self, x):
        parents = [y for y in self.o(x) if self.o(x)[y] == 'P' and
                   (y and '0' <= y[0] <= '9')]
        return parents[0] if parents else None

    def has_ancestor (self, *, ance, desc):
        x = desc
        if x == ance: return True
        while True:
            p = self.get_parent (x)
            if p:
                x = p
                if x == ance: return True
            else:
                break
        return False

    def link (self, a, b, linktype):
        if linktype not in ('PC', 'AB', ''):
            return '#linktype-err'
        # By type
        if linktype == '':
            self.set_link (a, b, '')
            self.set_link (b, a, '')
        elif linktype == 'PC':
            if a not in self.a() or b not in self.a():
                self.warn ('link PC: noexist')
                return '#link-noexist'
            if self.has_ancestor (ance=b, desc=a):
                self.warn ('link PC: cyclic')
                return '#link-cyclic'
            # Remove parent of b, if exists
            p = self.get_parent (b)
            if p:
                self.link (p, b, '')  # remove links
            self.set_link (a, b, 'C')
            self.set_link (b, a, 'P')
        elif linktype == 'AB':
            if a not in self.a() or b not in self.a():
                self.warn ('link PC: noexist')
                return '#link-noexist'
            # TODO take care of order
            self.set_link (a, b, 'B')
            self.set_link (b, a, 'A')

    def set_link (self, a, b, t):
        if a not in self.a(): return
        home = self.o(a)
        home[b] = t
        if not t:
            del home[b]

    def color (self, content, setting):
        if setting is None:
            return f'\x1b[0m{content}'
        else:
            (fg, bg) = setting
            return f'\x1b[{fg};{bg}m{content}\x1b[0m'

    def add_item (self, content):
        self.data['count'] += 1
        count = self.data['count']
        self.a()[str(count)] = self.init_item (content)
        self.log('add', str(count), content)
        return str(count)

    def done_item (self, idn, status='done'):
        idn = idn.strip()
        if idn not in self.data['a']:
            self.warn ('ID', idn, 'not found')
        else:
            self.o(idn)['s'] = status
            self.log ('done', idn, status)

    def remove_item (self, idn):
        # TODO unlink

        idn = idn.strip()
        if idn not in self.a():
            self.warn ('ID', idn, 'not found')
        else:
            del self.a()[idn]
            self.log ('remove', idn)

    def modify_item (self, idn, content):
        self.o(idn)['c'] = content

    def log (self, *args):
        line = json.dumps ([time.time(), *args], separators=(',',':'))
        print (line, file=self.log_file)

    def warn (self, *args):
        print (*args, file=sys.stderr)

    def __init__ (self):
        # FILE and LOG can be customized.
        self.FILE = './todo.json'
        self.LOG = './log.ndjson'

    def setup (self):
        # Setup file and log
        
        self.log_file = open (self.LOG, 'a')

        try:
            with open (self.FILE, 'r') as f:
                self.data = json.load (f)
        except FileNotFoundError:
            self.init_todo_repo ()
            
    def a (self):
        return self.data['a']

    def o (self, idn):
        return self.a()[idn]

    def close (self):
        # Save and exit
        with open (self.FILE, 'w') as f:
            json.dump (self.data, f, separators=(',',':'))

        self.log_file.close()

    def do_command (self, cmd):
        parts = cmd.split()
        return self.do_command_raw (parts)

    def do_command_raw (self, parts):
        if not parts:
            return
        
        head = parts[0]
        tails = parts[1:]
        tail = ' '.join(tails)

        if head == 'q':
            return '#break'
        elif head == 'a':
            self.add_item (tail)
        elif head == 'x':
            self.remove_item (tail)
        elif head == 'd':
            self.done_item (tail)
        elif head == 't':
            self.done_item (tail, status='todo')
        elif head == 'o':
            self.done_item (tail, status='outd')
        elif head == 'm':
            if len (tails) < 2: print ('Too few args')
            else:
                [idn, *content] = tails
                if idn not in self.a():
                    print ('No such id', idn)
                else:
                    self.modify_item (idn, ' '.join(content))
        elif head == 'p':
            if len (tails) != 2: print ('Num of args != 2')
            else:
                [a, b] = tails
                self.link (a, b, 'PC')
        elif head == 'l':
            if len (tails) != 2: print ('Num of args != 2')
            else:
                [a, b] = tails
                self.link (a, b, 'AB')
        elif head == 'b':
            if len (tails) != 2: print ('Num of args != 2')
            else:
                [a, b] = tails
                self.link (a, b, '')
        else:
            print ('Unidentified command', parts)

    def display (self):
        # Prints current self
        self.width = len(str(self.data['count']))

        for (idn, row) in self.a().items():
            if not self.get_parent (idn):
                self.display_tree (idn)

    def display_tree (self, idn, indent=0):
        print ('    ' * indent, end='')
        print (
            self.badge (idn),
            # self.o(idn)['s'],   # status implicit
            self.o(idn)['c'],
        )
        # If dependencies, print them
        pre = []
        post = []
        children = []
        for lnk in self.o(idn):
            if lnk and '0' <= lnk[0] <= '9':
                # link
                typ = self.o(idn)[lnk]
                if typ == 'C':
                    children.append(lnk)
                elif typ == 'A':
                    pre.append(lnk)
                elif typ == 'B':
                    post.append(lnk)

        if pre:
            print ('    ' * (indent+1), '<- ', ' '.join(self.badge (x) for x in pre), sep='')
        if post:
            print ('    ' * (indent+1), '-> ', ' '.join(self.badge (x) for x in post), sep='')
        for ch in children:
            self.display_tree (ch, indent = indent+1)

    def badge (self, number):
        status = self.o(number)['s']
        color = {
            'todo': (30, 101),
            'done': (97, 44),
            'outd': (37, 0),
        }.get (status, None)
        return self.color (' '+number.rjust(self.width)+' ', color)

    def main (self):
        args = sys.argv[1:]

        if not args:
            # Interactive
            self.setup ()
            self.display ()
            print()

            while True:
                cmd = input ('+ ')  # prompt
                result_value = self.do_command (cmd)
                if result_value == '#break': break
                print()
                self.display ()
                print()

            self.close ()
        else:
            # Command-line, run one command
            self.setup ()
            self.do_command_raw (args)
            print()
            self.display ()
            print()
            self.close ()

if __name__ == '__main__':
    Cation().main()

