# Contributing

Thanks for your interest. This is a pretty simple project, so there's not much to it.

## Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management. To install Poetry, run:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

or on Windows:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Then, install the dependencies:

```bash
poetry install
```

## Local Development

You can easily add this library to your own project using Poetry:

```bash
poetry add ../path/to/this/library
```

## Testing

Tests don't currently exist for this library. If you'd like to add them, please do!
