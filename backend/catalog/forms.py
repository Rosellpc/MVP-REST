from django import forms

from .models import Product


ALLERGENS = (
    "Gluten", "Crustáceos", "Huevo", "Pescado", "Cacahuetes", "Soja",
    "Lácteos", "Frutos secos", "Apio", "Mostaza", "Sulfitos", "Sésamo",
    "Moluscos", "Altramuz",
)


class ProductAdminForm(forms.ModelForm):
    selected_allergens = forms.MultipleChoiceField(
        label="Alérgenos presentes",
        choices=[(name, name) for name in ALLERGENS],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Selecciona los alérgenos confirmados del producto. No marcar opciones no significa que esté libre de alérgenos.",
    )
    allergens = forms.CharField(
        label="Observaciones de alérgenos y posibles trazas",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text="Conserva aquí declaraciones adicionales, posibles trazas e información pendiente de verificar.",
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only exact standalone names are interpreted as selections. Never infer
        # presence from a sentence such as 'Sin gluten' or 'Puede contener huevo'.
        lines = (self.initial.get("allergens") or "").splitlines()
        self.initial["selected_allergens"] = [name for name in ALLERGENS if name in lines]
        self.initial["allergens"] = "\n".join(line for line in lines if line not in ALLERGENS)

    def clean(self):
        data = super().clean()
        if "selected_allergens" in data and "allergens" in data:
            selected = set(data["selected_allergens"])
            lines = [name for name in ALLERGENS if name in selected]
            if data["allergens"]:
                lines.append(data["allergens"])
            # Keep the existing text contract consumed by the public product page.
            data["allergens"] = "\n".join(lines)
        return data
