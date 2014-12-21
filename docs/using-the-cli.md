ok is most commonly used from the command line. Call `ok -h` at any time for a help screen. Call `ok --version` to see your installed version. Calling `ok` without any additional parameters is equivalent to `ok run default`.

## init






<!-- @TODO: Below from old readme -->

```bash
strap
strap [-h, --help] [--version] {init,run,cache} ...
```

Calling `strap` without any arguments is equivalent to `strap run default`.

### init

`strap init [-h, --help] [-d, --dest DEST] [-s, --silent] source`

`source` can either be a directory or a GitHub repo URI. `DEST` is an optional directory. If `DEST` is given, then `source` will be cloned or copied into it. If `DEST` is omitted, then `source` will either be cloned into the current working directory (if it is a URI) or "refreshed" (if it is a directory, the equivalent of `strap run install`).

**Examples**:

```bash
strap init ../somedir/otherdir/strap-this
strap init copy/this --dest ../to/here/and-then-strap-it
strap init -s https://github.com/willyg302/Parrot
strap init gh:willyg302/jarvis
strap init git@github.com:willyg302/jarvis.git -d ~/jarvis-test
```

### run

`strap run [-h, --help] [-d, --dir DIR] [-s, --silent] [tasks [tasks ...]]`

You can provide a list of one or more `tasks` to run. If given, `DIR` specifies the path to execute tasks from; it defaults to the current working directory. Note that calling `strap run` (no arguments) is equivalent to `strap run default`.

**Examples**:

```bash
strap
strap run sometask --silent
strap run task_a task_b also_do_this --dir from/this/directory
```

### cache

`strap cache [-h, --help] {clean,list}`

Use this command to manage strap's dependency cache. You can `list` currently known modules (including ones that have failed to install) and `clean` the cache to start anew.

### list

`strap list [-h, --help]`

List the available tasks defined in a project's `strapme.py`. By convention, functions beginning with an underscore are ignored.