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
        dejavu_fonts  # <-- Adds real clean TrueType fonts
        fontconfig
        tpm2-tss
        pkg-config
        openssl
        tpm2-tools
      ];
      shellHook = ''
      export FONTCONFIG_PATH="${pkgs.fontconfig.out}/etc/fonts"
      export XDG_DATA_DIRS="${pkgs.dejavu_fonts}/share:$XDG_DATA_DIRS"
    '';
    };
  };
}