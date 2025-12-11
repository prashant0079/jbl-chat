from django import forms


class MessageForm(forms.Form):
    body = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Type a message...",
            }
        ),
    )

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        body = body.strip()
        if not body:
            raise forms.ValidationError("Message cannot be empty.")
        return body
