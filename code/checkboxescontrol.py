from typing import Optional, Dict, List
from pywinauto.controls.uiawrapper import UIAWrapper
from code.pywinauto_helpers import find_control, find_controls_by_type


class CheckboxesControl:
    """
    Manage all checkboxes in a window.
    Find all checkboxes once, then activate/deactivate by name.
    """
    
    def __init__(self, window: UIAWrapper):
        """
        Initialize checkbox controller and find all checkboxes.
        
        Args:
            window: Parent window containing checkboxes
        """
        self.window = window
        self.checkboxes: Dict[str, UIAWrapper] = {}
        self.states: Dict[str, int] = {}
        
        # Find all checkboxes
        self._find_all_checkboxes()
        
        # Get initial states
        self._update_states()
    
    def _find_all_checkboxes(self):
        """Find all checkboxes in the window and store them by name."""
        print("Finding all checkboxes...")
        
        # Use find_controls to get all CheckBox controls
        checkbox_controls = find_controls_by_type(self.window, "CheckBox", debug=False)
        
        # Also check for Buttons with TogglePattern
        button_controls = find_controls_by_type(self.window, "Button", debug=False)
        
        # Add CheckBox controls
        for ctrl in checkbox_controls:
            name = ctrl.window_text().strip()
            if name:
                self.checkboxes[name] = ctrl
                print(f"  ✓ Found CheckBox: '{name}'")
        
        # Add Button controls that have TogglePattern
        for ctrl in button_controls:
            try:
                if ctrl.get_toggle_pattern() is not None:
                    name = ctrl.window_text().strip()
                    if name and name not in self.checkboxes:  # Avoid duplicates
                        self.checkboxes[name] = ctrl
                        print(f"  ✓ Found Toggle Button: '{name}'")
            except AttributeError:
                pass
        
        print(f"\nTotal checkboxes found: {len(self.checkboxes)}")
    
    def _update_states(self):
        """Update the current state of all checkboxes."""
        for name, checkbox in self.checkboxes.items():
            try:
                state = checkbox.get_toggle_state()  # 0=Off, 1=On, 2=Indeterminate
                self.states[name] = 1 if state == 1 else 0
            except Exception as e:
                print(f"  ⚠️ Could not read state of '{name}': {e}")
                self.states[name] = None
    
    def get_all_names(self) -> List[str]:
        """Get list of all checkbox names."""
        return list(self.checkboxes.keys())
    
    def get_checkbox(self, name: str, exact: bool = False) -> Optional[UIAWrapper]:
        """
        Get a checkbox control by name using find_control.
        """
        return find_control(
            window=self.window,
            control_type="CheckBox",
            control_name=name,
            exact=exact,
            debug=False
        )
    
    def get_state(self, name: str, exact: bool = False) -> Optional[int]:
        """Get current state of a checkbox by name."""
        checkbox = self.get_checkbox(name, exact)
        
        if checkbox:
            try:
                state = checkbox.get_toggle_state()
                return 1 if state == 1 else 0
            except:
                return None
        
        return None
    
    def check(self, name: str, exact: bool = False) -> bool:
        """Check (activate) a checkbox by name."""
        return self._set_state(name, desired_state=1, exact=exact)
    
    def uncheck(self, name: str, exact: bool = False) -> bool:
        """Uncheck (deactivate) a checkbox by name."""
        return self._set_state(name, desired_state=0, exact=exact)
    
    def toggle(self, name: str, exact: bool = False) -> bool:
        """Toggle a checkbox by name."""
        checkbox = self.get_checkbox(name, exact)
        
        if not checkbox:
            print(f"  ⚠️ Checkbox not found: '{name}'")
            return False
        
        try:
            self.window.set_focus()
            checkbox.toggle()
            
            # Update state
            self._update_states()
            
            checkbox_name = checkbox.window_text()
            new_state = "checked" if self.get_state(name, exact) == 1 else "unchecked"
            print(f"  ✓ Toggled '{checkbox_name}' → {new_state}")
            return True
            
        except Exception as e:
            print(f"  ⚠️ Error toggling '{name}': {e}")
            return False
    
    def _set_state(self, name: str, desired_state: int, exact: bool = False) -> bool:
        """Set checkbox to a specific state."""
        checkbox = self.get_checkbox(name, exact)
        
        if not checkbox:
            print(f"  ⚠️ Checkbox not found: '{name}'")
            return False
        
        checkbox_name = checkbox.window_text()
        current_state = self.get_state(name, exact)
        
        if current_state is None:
            print(f"  ⚠️ Cannot read state of '{checkbox_name}'")
            return False
        
        # Already in desired state
        if current_state == desired_state:
            state_name = "checked" if desired_state == 1 else "unchecked"
            print(f"  ✓ '{checkbox_name}' already {state_name}")
            return True
        
        # Toggle to desired state
        try:
            self.window.set_focus()
            checkbox.toggle()
            
            # Update state
            self._update_states()
            
            state_name = "checked" if desired_state == 1 else "unchecked"
            print(f"  ✓ {state_name.capitalize()} '{checkbox_name}'")
            return True
            
        except Exception as e:
            print(f"  ⚠️ Error setting '{checkbox_name}': {e}")
            return False
    
    def get_checked(self) -> List[str]:
        """Get list of all checked checkbox names."""
        self._update_states()
        return [name for name, state in self.states.items() if state == 1]
    
    def get_unchecked(self) -> List[str]:
        """Get list of all unchecked checkbox names."""
        self._update_states()
        return [name for name, state in self.states.items() if state == 0]
    
    def print_summary(self):
        """Print summary of all checkboxes and their states."""
        self._update_states()
        
        print("\n" + "=" * 70)
        print("Checkbox Summary")
        print("=" * 70)
        
        for name, state in self.states.items():
            if state is None:
                status = "?"
                icon = "⚠️"
            elif state == 1:
                status = "checked"
                icon = "☑"
            else:
                status = "unchecked"
                icon = "☐"
            
            print(f"{icon} {name:50} [{status}]")
        
        print("=" * 70)
        print(f"Total: {len(self.checkboxes)} checkboxes "
              f"(✓ {len(self.get_checked())} checked, "
              f"✗ {len(self.get_unchecked())} unchecked)")
        print("=" * 70 + "\n")