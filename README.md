# Discord-bot

This is a custom discord-bot used for my personal servers.

This bot defines the following modules with multiple commands:

- `Help`: Module to handle help message.
- `Gambling`: Module containing all random based commands.
- `Music`: Module containing all commands used to play Youtube musics.

To get more informations on the multiple commands available, use the `/help`
command on the discord server directly.

For any feedbacks, bugs or new ideas, feel free to open a issue on this
repository so that we can discuss it ! :)

## Usage

This project require that the `ffmpeg-full` and `opus` are installated on
your machine.

If you are using [Nix Package Manager / Nixos](https://nixos.org/), you can pop
a shell with those requirements, bu running:

```sh
nix-shell
```

This project is also using [Poetry](https://github.com/python-poetry/poetry) to
manage his Python dependencies.

To enter a shell with all proper Python libraries setup, run:

```sh
poetry shell
poetry install
```

Finally, you need to define the following environment variables before running
the bot:

- `TOKEN`: The secret token used to connect to discord servers.
- `OPUS_LIBRARY_PATH`: The full path to the `libopus.so` file.

Once this is done, the bot can be started by running the following command:

```sh
poetry run bot
```
