{
  description = "A stupid simple devshell";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
  let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [
        uv
        python314
        python314Packages.customtkinter
        python314Packages.tpm2-pytss
        python314Packages.python-dotenv
        python314Packages.cryptography
        libglvnd
        libxkbcommon
        tpm2-tss
        pkg-config
        openssl
        chromium
      ];
      shellHook = ''
        export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.libglvnd pkgs.mesa ]}:$LD_LIBRARY_PATH"
      '';
    };
  };
}