# Validation evidence

## 2026-10-29

- Local GCC C++17, warnings as errors: ABI layout/rejection and FrameEpoch tests passed.
- Local preparation: repeat application yields identical manifest; unrelated edits are rejected and preserved.
- Windows run 40859763108, job 123399729080: diagnostics DLL and test programs compile;
  both CTest tests pass, including actual DLL loading and D3D11 resource introspection on WARP.
- Same run, host job: stopped before CMake at `git apply` due to CRLF in checked-out patch.
  Fix: normalize patch input bytes to LF, preserve exact context matching; configure fresh
  CS checkout with core.autocrlf=false. Regression: CRLF patch applied to fresh pinned
  source, reapplied, and checked for unrelated-edit rejection locally.
- Full CS host MSVC result still pending the next run. No Skyrim or hardware DXR run.
