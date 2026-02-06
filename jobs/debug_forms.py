# jobs/debug_forms.py
def debug_form_errors(form):
    """Функция для детальной отладки ошибок формы"""
    if not form.is_valid():
        print("\n" + "="*50)
        print("FORM DEBUG INFO")
        print("="*50)
        print(f"Form is valid: {form.is_valid()}")
        print(f"Errors: {form.errors}")
        
        # Детальная информация по полям
        for field_name, field in form.fields.items():
            if field_name in form.errors:
                print(f"\nField: {field_name}")
                print(f"Label: {field.label}")
                print(f"Required: {field.required}")
                print(f"Errors: {form.errors[field_name]}")
                
        # Информация о данных формы
        print(f"\nForm data:")
        for field_name, value in form.data.items():
            print(f"  {field_name}: {value}")
        
        print("="*50 + "\n")
        return False
    return True