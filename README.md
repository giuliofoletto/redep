# Redep

Redep is a simple tool to push and pull a directory to multiple remote machines.
Local copying is also supported.
It is especially useful if you want to test changes on a remote host without setting up a full deployment pipeline, or version control.

## Usage

Initialize a configuration file in the directory you want to push or into which you want to pull:

```bash
redep init
```

Edit the generated `redep.toml` file to add your remote machines and to specify the paths to push or pull.
An empty host (`host = ""`) indicates local copying.

Push the directory:

```bash
redep push
```

Pull into the directory:

```bash
redep pull
```

Whenever you change something and want to redeploy, just run the push command again.

## Roadmap

Next planned features:

-   Pull from Windows machines.
-   Pull from multiple hosts.
-   Full cross-platform support.

## Acknowledgements

This project uses [Fabric](https://www.fabfile.org/) for remote operations.
