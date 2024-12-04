### **How to execute image descriptions directly or with function call**


1. **At the Bottom of the Script (Standalone Test):**
   - Place the `# Example usage` block at the **very bottom** of the script after all function definitions.
   - This ensures that the script executes the test code only when run directly (not when imported as a module into another script).

   **Example:**
   ```python
   # Place the following at the bottom of your script:

   if __name__ == "__main__":
       image_path = "example_image.jpg"  # Replace with the path to your image
       try:
           summary = get_image_summary(image_path)
           print(f"Image Summary: {summary}")
       except Exception as e:
           print(f"An error occurred: {e}")
   ```

2. **Testing the Script:**
   - Save your script with all the extracted functions and the example usage block at the bottom.
   - Run the script in your terminal or IDE:
     ```bash
     python your_script_name.py
     ```
   - Replace `"example_image.jpg"` with the path to an actual image file you want to summarize.

3. **Purpose of the Example Usage Block:**
   - Demonstrates how the `get_image_summary` function works in practice.
   - Helps you test if the function behaves as expected without integrating it into larger systems.

---

### **Using It in a Larger Program**

If your script is part of a larger project:
- Remove or comment out the `if __name__ == "__main__":` block after testing.
- Call `get_image_summary(image_path)` directly from other parts of your program where it’s needed.

   **Example Integration in Another Script:**
   ```python
   from your_script_name import get_image_summary

   image_path = "path_to_some_image.jpg"
   summary = get_image_summary(image_path)
   print(f"Summary of the image: {summary}")
   ```

This flexibility allows you to test the function independently and use it modularly in larger systems.