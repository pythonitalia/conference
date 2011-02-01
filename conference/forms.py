# -*- coding: UTF-8 -*-
from django import forms
from conference import models

class SubmissionForm(forms.Form):
    activity = forms.CharField(max_length=50, required=False)
    industry = forms.CharField(max_length=50, required=False)
    bio = forms.CharField(widget=forms.Textarea())

    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 40}))
    duration = forms.TypedChoiceField(choices=models.TALK_DURATION, coerce=int, initial='30')
    language = forms.TypedChoiceField(choices=models.TALK_LANGUAGES, initial='en')
    slides = forms.FileField(required=False)
    abstract = forms.CharField(widget=forms.Textarea())
