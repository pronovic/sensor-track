# TODO:

- [x] Unit test code in `dispatcher.py`
- [x] Add to_yaml() and from_yaml() on `LifecycleConverter`
- [x] Unit tests for serializing and deserializating `SmartAppDefinition`
- [x] Figure out where to add Python logging under `smartapp`
- [ ] Wire up FastAPI to accept requests and forward to dispatcher
- [ ] Create a dummy SmartApp and start integration testing the full flow
- [ ] Capture digital signature data from the integration test messages
- [ ] Implement digital signature checking, initially for only RSA-SHA256