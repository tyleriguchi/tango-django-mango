from django.contrib import admin
from rango.models import Category, Page, UserProfile
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'views', 'likes')
	ordering = ['-views']

class PageAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'url')
	ordering = ['title']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(UserProfile)
