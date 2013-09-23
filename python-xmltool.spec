%define modname xmltool
%define version 0.3.2
%define unmangled_version 0.3.3
%define unmangled_version 0.3.3
%define release 1

Summary: Tool to manipulate XML files
Name: python-xmltool
Version: %{version}
Release: %{release}
Source0: http://pypi.python.org/packages/source/t/%{modname}/%{modname}-%{version}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{modname}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Aurélien Matouillot <a.matouillot@gmail.com>
Url: http://xmltool.lereskp.fr/
Requires: python-lxml
Requires: python-webob

%description
xmltool
=========

xmltool is a python package to manipulate XML files. It's very useful to update some XML files with the python syntax without using the DOM.
The main goal of this package was to create a HTML form to edit and create a XML file. The form generation is based on a dtd file.
`Read the documentation <http://xmltool.lereskp.fr>`_


Changelog
=========

O.3.3:
    * Fix missing require

O.3.2:
    * Better support for local dtd. It can a relative path from the XML filename.
    * Bug fix: the EMPTY tags are support correctly!

O.3.1:
    * Render the text element as HTML format when exporting in XML (no autoclose tag)
    * Bug fix: make sure we add empty text element in the HTML form

O.3:
    * Rewrite the core of the code
    * Better performance to generate the HTML
    * Bug fix

O.2:
    * Update the project architecture
    * Be able to access to the element properties like a dict
    * Add functions to easily update or create XML file
    * Fix missing README file in the package

O.1:
    * Initial version: package to manipulate XML file and create HTML forms.


%prep
%setup -n %{modname}-%{unmangled_version} -n %{modname}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
