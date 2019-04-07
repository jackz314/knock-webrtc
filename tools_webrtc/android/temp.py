#!/usr/bin/env python


def main():
  print("Starting aar build...\n")
  args = _ParseArgs()
  # logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO)
  logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if args.verbose else logging.INFO)

  BuildAar(args.arch, args.output, args.use_goma, args.extra_gn_args,
           args.build_dir, args.extra_gn_switches, args.extra_ninja_switches)


if __name__ == '__main__':
  sys.exit(main())
