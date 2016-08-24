'''Command line interface to Legofy'''
import click
import legofy
from legofy import palettes


@click.command()
@click.argument('image', required=True, type=click.Path(dir_okay=False,
                                                        exists=True,
                                                        resolve_path=True))
@click.argument('output', default=None, required=False,
                type=click.Path(resolve_path=True))
@click.option('--size', default=None, type=int,
              help='Number of bricks the longest side of the legofied image should have.')
@click.option('--dither/--no-dither', default=False,
              help='Use dither algorithm to spread the color approximation error.')
@click.option('--palette', default=None,
              type=click.Choice(palettes.legos().keys()),
              help='Palette to use based on real Lego colors.')
@click.option('--optimize/--no-optimize', default=False,
              help='Minimize the number of bricks used by using bigger bricks.')

def main(image, output, size, palette, dither, optimize):
    '''Legofy an image!'''
    legofy.main(image, output_path=output, size=size,
                palette_mode=palette, dither=dither, minimize_bricks_number=optimize)

if __name__ == "__main__":
  main()