# coding: utf-8
"""
The MIT License

Copyright (c) 2009 Marici, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
from django import forms
from django.conf import settings
from django.utils.http import int_to_base36
from django.template import loader, Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.contrib.localflavor.jp.jp_prefectures import JP_PREFECTURES
from recipebook.maricilib.django.apps.taskqueue.queue import get_taskqueue
from recipebook.maricilib.django.apps.taskqueue.tasks import SendEmailTask
import models

GENDER_CHOICES = (("female", "女"), ("male", u"男"))
BIRTHYEAR_CHOICES = [ (str(y), str(y)) for y in range(1900, 1999) ]
NUM_PEOPLE_CHOICES = (("1", "1人分"), ("2", "2人分"),
                      ("3", "3人分"), ("4", "4人分"))

def _text_input(size):
    return forms.TextInput(attrs={"size":size})
                           
def _text_area(rows, cols):
    return forms.Textarea(attrs={"rows":rows, "cols":cols})

def get_contest_choices():
    return [ (str(contest.pk), contest.name) for contest 
            in models.Contest.objects.get_current_contests() ]
    
def email_to_username(email):
    if not email:
        return ""
    return email.replace("@", "_at_").replace(".", "_")

class AuthenticationForm(forms.Form):
    """
    ログインフォーム
    """
    email = forms.EmailField(label=u"メールアドレス", max_length=30)
    password = forms.CharField(label=u"パスワード", widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            username = email_to_username(email)
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(u"メールアドレスとパスワードをもう一度確認してください。")
            elif not self.user_cache.is_active:
                raise forms.ValidationError(u"このアカウントは有効ではありません。")

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class UserCreationForm(forms.ModelForm):
    """
    新規にユーザ登録するフォーム。
    必須項目は以下の通りです。
    email: 任意の文字列 (20文字以内)
    password1: 任意の文字列
    password2: password1と同じ文字列
    nickname: 任意の文字列
    gender: male/female
    birth_year: 1900から1999までの整数
    prefecture: JP_PREFECTURESで定義された文字列
    agree_tos: trueであること
    """

    class Meta:
        model = User
        fields = ("email", "firstname")
        
    email = forms.EmailField(label=u"メールアドレス", 
                             help_text=u"メールアドレスは公開されません。")
    password1 = forms.CharField(label=u"パスワード", widget=forms.PasswordInput)
    password2 = forms.CharField(label=u"パスワードの確認", widget=forms.PasswordInput)
    first_name = forms.CharField(label=u"ニックネーム", 
                               help_text=u"ニックネームは公開されます。後で変更できます。")
    gender = forms.ChoiceField(label=u"性別", choices=GENDER_CHOICES,
                               widget=forms.RadioSelect, initial="female",
                               help_text=u"性別は公開されません。")
    birth_year = forms.IntegerField(label="誕生年", 
                                    widget=forms.Select(choices=BIRTHYEAR_CHOICES),
                                    initial=1970,
                                    help_text=u"誕生年は公開されません。")
    prefecture = forms.ChoiceField(label=u"住所", choices=JP_PREFECTURES,
                                   initial="tokyo",
                                   help_text=u"住所は公開されません。")
    agree_tos = forms.BooleanField(label=u"規約に同意する", required=False)    

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(u"同じメールアドレスが既に登録済みです。")
    
    def clean_agree_tos(self):
        agree = self.cleaned_data["agree_tos"]
        if not agree:
            raise forms.ValidationError(u"利用規約に同意しなければ登録できません。")
        return agree
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(u"二つのパスワードが一致しません。")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = email_to_username(self.cleaned_data["email"])
        user.first_name = self.cleaned_data["first_name"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
        
    def get_profile_dict(self):
        is_female = (self.cleaned_data["gender"] == "female")
        return {"is_female":is_female,
                "birth_year":self.cleaned_data["birth_year"],
                "prefecture":self.cleaned_data["prefecture"]
                }


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = models.UserProfile
        exclude = ("validation_key", "is_female", "birth_year")
        
    prefecture = forms.ChoiceField(label=u"住所", choices=JP_PREFECTURES,
                                   help_text=u"住所は公開されません。")
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs) 
        self.fields["profile_text"].widget = _text_area(3, 60)
        self.fields["blog_url"].widget = _text_input(40)

class PasswordResetForm(auth_forms.PasswordResetForm):
    
    def save(self, domain_override=None, email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator):
        """
        Generates a one-use only link for resetting password and sends to the user
        """
        for user in self.users_cache:
            if not domain_override:
                current_site = Site.objects.get_current()
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            t = loader.get_template(email_template_name)
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            task = SendEmailTask(dict(subject=u"[%s] パスワードをリセット" % site_name, 
                                      body=t.render(Context(c)), 
                                      from_address=settings.EMAIL_FROM,
                                      to_list=[user.email]))
            get_taskqueue().send_task(task, queue_name=settings.QUEUENAME_EMAIL)


class NewRecipeForm(forms.ModelForm):
    """
    新規にレシピを作成するフォーム。
    必須項目は以下の通りです。
    name: 任意の文字列 (20文字以内)
    introduction: 任意の文字列
    非必須項目は以下の通りです。
    photo: 画像ファイルパス
    feeling: models.Feelingのname値
    """
    class Meta:
        model = models.Recipe
        exclude = ("ingredients", "tips", "is_draft", "is_awarded", "num_people")

    def __init__(self, *args, **kwargs):
        super(NewRecipeForm, self).__init__(*args, **kwargs) 
        self.fields["name"].widget = _text_input(40)
        self.fields["introduction"].widget = _text_area(5, 60)

class RecipeForm(forms.ModelForm):
    """
    レシピを編集するフォーム。
    項目はNewRecipeFormと同様です。
    違いは非必須項目に以下を含むことです。
    tips: 任意の文字列
    """
    class Meta:
        model = models.Recipe
        exclude = ("ingredients", "is_draft", "is_awarded")
    
    num_people = forms.ChoiceField(label=u"分量の人数", 
                                   choices=NUM_PEOPLE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs) 
        self.fields["name"].widget = _text_input(40)
        self.fields["introduction"].widget = _text_area(5, 60)
        self.fields["tips"].widget = _text_area(3, 60)

class BackendRecipeForm(forms.ModelForm):
    class Meta:
        model = models.Recipe
        exclude = ("is_draft", "is_awarded")

class DirectionForm(forms.ModelForm):
    """
    作り方を作成するフォーム。
    必須項目は以下の通りです。
    text: 任意の文字列
    非必須項目は以下の通りです。
    photo: 画像ファイルパス
    """
    class Meta:
        model = models.Direction
        
    def __init__(self, *args, **kwargs):
        super(DirectionForm, self).__init__(*args, **kwargs) 
        self.fields["text"].widget = _text_area(3, 60)

class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs) 
        self.fields["text"].widget = _text_area(3, 60)
        
        
class SubmitToContestForm(forms.Form):
    contest = forms.ChoiceField(label=u"お題")

    def __init__(self, *args, **kwargs): 
        super(SubmitToContestForm, self).__init__(*args, **kwargs) 
        self.fields["contest"].widget.choices = get_contest_choices()


class EmailChangeForm(forms.Form):
    """
    メールアドレス変更フォーム
    """
    email = forms.EmailField(label=u"メールアドレス", max_length=30)
    
    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(u"同じメールアドレスが既に登録済みです。")
    
