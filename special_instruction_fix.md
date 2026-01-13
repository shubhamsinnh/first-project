Fix: Special Functionality
- Added `toggleSpecialInstructions` function to show/hide the input field when the checkbox is toggled.
- Added `id="special-instructions-text"` to the textarea to allow JavaScript to access its value.
- Updated `addToCart` function to capture the special instructions text and save it to the cart object in localStorage.

Verification:
- Toggled the checkbox -> input field appeared.
- Typed text -> added to cart.
- Verified localStorage -> `specialInstructions` field is present in the cart item.
