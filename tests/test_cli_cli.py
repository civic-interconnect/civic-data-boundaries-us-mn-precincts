from typer.testing import CliRunner

from civic_data_boundaries_us_mn_precincts.cli.cli import app

runner = CliRunner()


def test_index():
    result = runner.invoke(app, ["index"])

    # Debug output
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exception(
                type(result.exception), result.exception, result.exception.__traceback__
            )

    assert result.exit_code == 0
