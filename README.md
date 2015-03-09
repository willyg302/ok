<p align="center">
	<img width="379" height="250" src="https://raw.github.com/willyg302/ok/master/ok-logo.png" alt="ok" title="Everything is going to be ok">
</p>

-----

[![license](http://img.shields.io/badge/license-MIT-red.svg?style=flat-square)](https://raw.githubusercontent.com/willyg302/ok/master/LICENSE)

ok is Make for stupid people: a simple tool for cloning, copying, and initializing projects, because bootstrapping shouldn't be so gosh-durn hard. Inspired by [init-skeleton](https://github.com/paulmillr/init-skeleton).

## Install

ok assumes you have at least [Python 2.7](https://www.python.org/) and [git](http://git-scm.com/) installed. You can check whether you have these dependencies with the following commands:

```bash
$ python --version
$ git --version
```

If those return version strings and not errors, you're good to go!

1. Using git, clone ok to somewhere convenient (for this readme, we will assume your home directory):

   ```bash
   $ git clone git@github.com:willyg302/ok.git
   ```

   ...or if you wish, download and unpack the ZIP from [GitHub](https://github.com/willyg302/ok).

2. Run the following commands, following any additional instructions you receive along the way:

   ```bash
   $ cd ok
   $ python install.py
   ```

Congratulations, you're now ready to use ok!

## Testing

Call `ok run test` while in the root directory of this repo. Yes, ok uses itself to test itself. No, you should not be surprised.

## Roadmap (v0.5.0)

- [ ] Basic tests
- [x] Code rewrite to be completely bootstrapping
- [x] Split modules into separate repository, remove Python-centric code
- [ ] Set up documentation
- [x] Support Python 3.4
