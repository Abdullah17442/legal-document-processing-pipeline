import hashlib


def calculate_file_hash(file):
    """
    Calculate SHA-256 hash of a file object.

    The file pointer is reset to the beginning
    after hashing so the file can be read again.
    """

    sha256 = hashlib.sha256()

    while True:

        chunk = file.read(1024 * 1024)

        if not chunk:
            break

        sha256.update(chunk)

    # Reset file pointer so the file can be
    # read again later by the upload pipeline.
    file.seek(0)

    return sha256.hexdigest()