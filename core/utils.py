--- a/.gitignore+++ b/.gitignore@@ -31,3 +31,7 @@ # OS
 .DS_Store
 Thumbs.db
+
+# Environment files
+.env
+.env.*
--- a/core/views.py+++ b/core/views.py@@ -57,6 +57,9 @@         'recent_bills': Bill.objects.all().order_by('-last_updated')[:5],
         'recent_events': Event.objects.all().order_by('-date')[:5],
         'monitored_measures': monitored_data,
+        'keywords': Keyword.objects.all().order_by('term'),
+        'comms': MonitoredCommission.objects.filter(is_active=True).order_by('name'),
+        'available_commissions': sorted(AVAILABLE_COMMISSIONS),
     }
     return render(request, 'core/dashboard.html', context)
@@ -314,9 +317,18 @@
 def delete_item(request, item_type, item_id):
-    model_map = {'keyword': Keyword, 'measure': MonitoredMeasure, 'commission': MonitoredCommission, 'preset': NewsPreset}
-    if item_type in model_map:
-        get_object_or_404(model_map[item_type], id=item_id).delete()
-    return redirect('configuracion')
+    model_map = {
+        'keyword': Keyword,
+        'measure': MonitoredMeasure,
+        'commission': MonitoredCommission,
+        'preset': NewsPreset,
+    }
+    if item_type in model_map:
+        get_object_or_404(model_map[item_type], id=item_id).delete()
+
+    # Redirección según área
+    if item_type in {'keyword', 'measure', 'commission'}:
+        return redirect('dashboard_configuracion')
+    return redirect('configuracion')
--- a/core/templates/core/dashboard.html+++ b/core/templates/core/dashboard.html@@ -1,200 +1,200 @@
 {% extends 'core/base.html' %} 
 
 {% block content %}
 <div class="p-6 bg-gray-50 min-h-screen">
@@ -55,7 +55,7 @@
                 <div class="flex justify-between items-center bg-gray-50">
                     <h3 class="font-bold text-gray-700"><i class="fas fa-satellite-dish mr-2 text-purple-500"></i> Rastreador SUTRA (En Vivo)</h3>
-                    <a href="{% url 'configuracion' %}" class="text-xs text-blue-600 hover:underline">Configurar</a>
+                    <a href="{% url 'dashboard_configuracion' %}" class="text-xs text-blue-600 hover:underline">Configurar</a>
                 </div>
                 <div class="p-0">
                     {% if monitored_measures %}
@@ -160,7 +160,7 @@
                     <div class="flex flex-wrap gap-2 max-h-60 overflow-y-auto">
                         {% for comm in comms %}
                         <span class="inline-flex items-center bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-0.5 rounded-full border border-amber-200">
@@ -220,7 +220,7 @@
                 </form>
 
-                <form method="POST" action="{% url 'configuracion' %}" class="flex gap-2 items-center mb-3">
+                <form method="POST" action="{% url 'dashboard_configuracion' %}" class="flex gap-2 items-center mb-3">
                     {% csrf_token %}
                     <input type="text" name="keyword" placeholder="Añadir keyword" class="flex-1 px-3 py-2 border rounded-lg text-sm">
                     <button type="submit" name="add_keyword" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">
@@ -260,7 +260,7 @@
                 </form>
 
-                <form method="POST" action="{% url 'configuracion' %}" class="grid grid-cols-1 gap-2 mb-3">
+                <form method="POST" action="{% url 'dashboard_configuracion' %}" class="grid grid-cols-1 gap-2 mb-3">
                     {% csrf_token %}
                     <input type="text" name="measure_id" placeholder="Añadir medida (ej: P. de la C. 123)" class="px-3 py-2 border rounded-lg text-sm">
                     <button type="submit" name="add_measure" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">
@@ -320,7 +320,7 @@
                 </form>
 
-                <form method="POST" action="{% url 'configuracion' %}" class="flex gap-2 items-center mb-3">
+                <form method="POST" action="{% url 'dashboard_configuracion' %}" class="flex gap-2 items-center mb-3">
                     {% csrf_token %}
                     <select name="commission_name" class="flex-1 px-3 py-2 border rounded-lg text-sm">
                         {% for c in available_commissions %}
--- a/core/templates/core/dashboard_configuracion.html+++ b/core/templates/core/dashboard_configuracion.html@@ -1,9999 +1,9999 @@
 {% extends 'core/base.html' %}
 
 {% block content %}
 <div class="p-8 min-h-screen bg-[#f5f6fa]">
@@
 </div>
 {% endblock %}
--- a/requirements.txt+++ b/requirements.txt@@ -1,30 +1,30 @@
 Django==5.1.3
 dj-database-url==2.3.0
 google-generativeai==0.8.3
 requests==2.32.3
 beautifulsoup4==4.12.3
 feedparser==6.0.11
 lxml==5.3.0
 gunicorn==23.0.0
 python-dotenv==1.0.1
 urllib3==2.2.2
 psycopg2-binary==2.9.10
 django-allauth==65.0.1
 djangorestframework==3.15.2
 django-jazzmin==3.0.1
 django-unfold==0.76.0
 django-import-export==4.1.1
 django-environ==0.11.2
 django-cors-headers==4.4.0
 pgvector==0.3.6
 sentence-transformers==3.2.1
 torch==2.5.1
 transformers==4.46.3
 numpy==1.26.4
 scikit-learn==1.5.2
 python-dateutil==2.9.0.post0
 pandas==2.2.3
 rank-bm25==0.2.2
