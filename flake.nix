{
  description = "A stupid simple devshell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux"; # Change to "aarch64-macos" if you're on Apple Silicon
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python314
          python314Packages.python-dotenv
          python314Packages.cryptography
          python314Packages.tpm2-pytss
        ];
      };
    };
}