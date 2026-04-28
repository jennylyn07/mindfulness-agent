# v2 — voice journaling via Azure Blob Storage. One new class, zero agent changes.
# When implementing: create AzureBlobFileStore(IFileStore) and inject it where needed.
# The IFileStore interface is the only contract — all 6 agents remain completely untouched.
#
# Demo closing line:
# "Voice journaling is the natural next step — the file store provider is already
#  in the adapter layer. Adding it means writing one new class, with zero changes
#  to any of the six agents."


class IFileStore:
    """
    Interface for file storage operations.
    Implement AzureBlobFileStore for voice journaling (v2).
    """

    async def upload(self, file_id: str, data: bytes, content_type: str) -> str:
        """Upload a file. Returns the public URL."""
        raise NotImplementedError

    async def get_url(self, file_id: str) -> str:
        """Get the public URL for an existing file."""
        raise NotImplementedError

    async def delete(self, file_id: str) -> None:
        """Delete a file by ID."""
        raise NotImplementedError
