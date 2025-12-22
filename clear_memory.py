"""
Simple script to clear all JARVIS memories.
This deletes:
- jarvis_memory.db (WorkingMemory database)
- jarvis_state.json (SessionState file)
- memory.db (if exists)
"""
import os
import sys

def clear_memory():
    """Delete all memory files."""
    files_to_delete = [
        "jarvis_memory.db",
        "jarvis_state.json",
        "jarvis_core/jarvis_memory.db",
        "jarvis_core/jarvis_state.json",
        "memory.db",
        "jarvis_core/memory.db"
    ]
    
    deleted = []
    not_found = []
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted.append(file_path)
                print(f"✓ Deleted: {file_path}")
            except Exception as e:
                print(f"✗ Error deleting {file_path}: {e}")
        else:
            not_found.append(file_path)
    
    if deleted:
        print(f"\n✓ Successfully deleted {len(deleted)} memory file(s).")
    else:
        print("\n⚠ No memory files found to delete.")
    
    if not_found:
        print(f"\nℹ {len(not_found)} file(s) not found (may not exist):")
        for f in not_found:
            print(f"  - {f}")

if __name__ == "__main__":
    print("Clearing all JARVIS memories...\n")
    clear_memory()
    print("\nDone! All memories have been cleared.")
    print("Note: Make sure JARVIS is not running when clearing memory.")

