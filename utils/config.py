import toml

def read_toml_file(file_path):
    try:
        with open(file_path, 'r') as toml_file:
            data = toml.load(toml_file)
        return data
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
        return None
    except toml.TomlDecodeError as e:
        print(f"Error decoding TOML file: {e}")
        return None


