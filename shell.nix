{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  buildInputs = [
    pkgs.ffmpeg-full
    pkgs.libopus.out
  ];
}
