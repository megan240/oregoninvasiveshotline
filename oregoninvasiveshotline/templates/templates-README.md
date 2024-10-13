# Django Template Language (DTL) - Templates

This document should help gain a rough understanding of the hierarchy of templates in this codebase. It should give basic information in regards to creating <u>_Django Template Language Templates_</u>

## Table of Contents

## Template Hierarchy
The following is the hierarchy of the templates that exist in the Templates folder. The way the templates work, is that there are templates that form content within other templates. 
For Example:
The `home.html` extends the `base.html`
At the top of `home.html` we have the following:
```django
{% extends 'base.html' %}

{% load static %}
{% load pages %}

{% block main_class %}container-fluid{% endblock %}
{% block body_class %}white{% endblock %}
```
In this example It's going to take everything in base.html and utilize it.
It's then going to find 
```django
{% block main_class %}{% endblock %}
```
Same for the following:
```django
{% block body_class %}{% endblock %}
```

### `templates/`

1. #### `boostrapform/`

- - ##### `field.html`

2. #### `comments/`

- - ##### `_edit.html`
- - ##### `edit.html`

3. #### `flatpages/`

- - ##### `default.html`

4. #### `notifications/`

- - ##### `admin_list.html`
- - ##### `create.html`
- - ##### `edit.html`
- - ##### `email.txt`
- - ##### `list.html`
- - ##### `notify_new_owner.txt`

5. #### `registration/`

- - ##### `logged_out.html`
- - ##### `login.html`
- - ##### `password_change_done.html`
- - ##### `password_change_form.html`
- - ##### `password_reset_complete.html`
- - ##### `password_reset_confirm.html`
- - ##### `password_reset_done.html`
- - ##### `password_reset_form.html`
- - ##### `password_reset_subject.html`

6. #### `reports/`

- - ##### `search/`
- - - ###### `_fields.html`
- - - ###### `_sort.html`
- - ##### `_invite_expert.txt`
- - ##### `_legend_dialog.html`
- - ##### `_legend.html`
- - ##### `_list.html`
- - ##### `_list.js.html`
- - ##### `_new_comment.txt`
- - ##### `_popover.html`
- - ##### `_submission.txt`
- - ##### `claim.html`
- - ##### `create.html`
- - ##### `detail.html`
- - ##### `export.kml`
- - ##### `help.html`
- - ##### `list_public.html`
- - ##### `list.html`
- - ##### `unclaim.html`

7. #### `species/`

- - ##### `category_detail_form.html`
- - ##### `category_list.html`
- - ##### `list.html`
- - ##### `severity_detail_form.html`
- - ##### `severity_list.html`
- - ##### `species_detail_form.html`

8. #### `users/`

- - ##### `_login.txt`
- - ##### `avatar.svg`
- - ##### `edit.html`
- - ##### `home.html`
- - ##### `list.html`
- - ##### `user_detail.html`

#### `_admin_panel_nav.html`

Currently - when you are in the admin page, if you click the 'profile-button-icon' in top corner and then click 'admin', this is shown.

#### `_images.html`

Currently - when you are making a report, this is what shows up at the

#### `_pagination.html`

Currently - When you are searching for reports that have been made in the 'Search Reports' link, this is what allows the buttons at the bottom of the page, listing page number out of how many pages exist with the back-and-forth buttons.

#### `403.html`

#### `404.html`

#### `admin_panel.html`

`extends templates/base.html` `include _admin_panel.html`

#### `base.html`

currently - the !doctype html with all head information and the basic body. Has the logo-link at the top and the buttons at the top that serve as a "navigation". It also has the footer copyright. Depending if the user in logged in changes whether the 'log in' button displays or the username displays.

#### `delete.html`

#### `error.html`

#### `home.html`

#### `nav_tabs.html`
Currently - appear to be admin related to reports

