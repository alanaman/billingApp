from escpos.printer import Dummy

# Create a dummy printer instance
p = Dummy()

# Print test content
p.text("Hello, this is a test print!\n")
p.barcode('123456789012', 'EAN13', 64, 2, '', '')

# Get the ESC/POS command output
print(p.output.decode())  # Decoded raw ESC/POS commands
