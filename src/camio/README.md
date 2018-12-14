# Camera Input/Output Library

## Design choices

The goal of the library is act as a unified interface for different camera libraries.

### Adapter

Each library has its own adapter, which acts a the interface between the camio API and the underlying camera library API.

Each adapter can be enabled or disabled during build, to reduce dependencies to a minimum. 

### Frame

The returned frame object needs to be freed by the receiver.
