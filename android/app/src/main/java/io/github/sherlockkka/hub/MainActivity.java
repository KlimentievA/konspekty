package io.github.sherlockkka.hub;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Hub: сайт sherlockkka.github.io/konspekty во весь экран, без адресной строки.
 *  Содержимое всегда свежее (грузится с сайта), после первого запуска работает и без сети (кэш сайта). */
public class MainActivity extends Activity {
    static final String HOST = "sherlockkka.github.io";
    static final String HOME = "https://sherlockkka.github.io/konspekty/";
    WebView web;
    boolean offlineShown = false;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        web = new WebView(this);
        web.setBackgroundColor(getResources().getColor(R.color.bg, getTheme()));
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // оценки, заметки, настройки сайта (localStorage)
        s.setDatabaseEnabled(true);
        s.setTextZoom(100);                    // масштаб — кнопками A−/A+ на самом сайте
        s.setSupportZoom(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " HubApp/1");

        web.addJavascriptInterface(new Bridge(), "HubApp");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if (HOST.equals(u.getHost()) && u.getPath() != null && u.getPath().startsWith("/konspekty")) return false;
                if ("about".equals(u.getScheme()) || "data".equals(u.getScheme())) return false;
                openOutside(u);                // источники новостей, Мосбиржа и т.п. — во внешнем браузере
                return true;
            }

            @Override
            public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame() && !offlineShown) {
                    offlineShown = true;
                    String bg = isNight() ? "#171611" : "#F4F1E8", fg = isNight() ? "#E8E4D8" : "#25221C";
                    v.loadDataWithBaseURL(HOME, "<html><head><meta name=viewport content='width=device-width,initial-scale=1'></head>"
                        + "<body style='margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:" + bg + ";color:" + fg + ";font-family:sans-serif;text-align:center'>"
                        + "<div><div style='font:600 56px Georgia,serif;color:#A93D28'>§</div><h2 style='margin:10px 0 6px'>Нет соединения</h2>"
                        + "<p style='opacity:.7;margin:0 0 18px'>Проверь интернет и попробуй ещё раз.</p>"
                        + "<a href='" + HOME + "' style='padding:12px 22px;border-radius:999px;background:#1F6B57;color:#fff;text-decoration:none'>Повторить</a></div></body></html>",
                        "text/html", "utf-8", null);
                }
            }

            @Override
            public void onPageFinished(WebView v, String url) {
                if (url != null && url.startsWith("http")) offlineShown = false;
                // цвет полосы статуса = фон сайта (с учётом выбранной на сайте темы)
                v.evaluateJavascript("(function(){function f(){try{HubApp.bar(getComputedStyle(document.body).backgroundColor)}catch(e){}}"
                    + "f();if(!window.__hubObs){window.__hubObs=1;new MutationObserver(function(){setTimeout(f,50)}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme','class','style']});"
                    + "try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){setTimeout(f,50)})}catch(e){}window.addEventListener('hashchange',function(){setTimeout(f,100)})}})()", null);
            }
        });
        web.setDownloadListener((url, ua, cd, mime, len) -> openOutside(Uri.parse(url)));

        if (state != null) web.restoreState(state);
        else load(getIntent());
    }

    void load(Intent i) {
        Uri d = i != null ? i.getData() : null;
        web.loadUrl(d != null && HOST.equals(d.getHost()) ? d.toString() : HOME);
    }

    @Override
    protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        if (i.getData() != null) load(i);
    }

    boolean isNight() {
        return (getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)
            == android.content.res.Configuration.UI_MODE_NIGHT_YES;
    }

    void openOutside(Uri u) {
        try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (ActivityNotFoundException ignored) { }
    }

    class Bridge {
        @JavascriptInterface
        public void bar(String css) {
            runOnUiThread(() -> {
                try {
                    String[] p = css.replaceAll("[^0-9,.]", "").split(",");
                    int r = (int) Float.parseFloat(p[0]), g = (int) Float.parseFloat(p[1]), b = (int) Float.parseFloat(p[2]);
                    int c = Color.rgb(r, g, b);
                    Window w = getWindow();
                    w.setStatusBarColor(c);
                    w.setNavigationBarColor(c);
                    web.setBackgroundColor(c);
                    boolean light = (0.299 * r + 0.587 * g + 0.114 * b) > 150;
                    View dv = w.getDecorView();
                    int f = dv.getSystemUiVisibility();
                    f = light ? (f | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR) : (f & ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
                    if (Build.VERSION.SDK_INT >= 26)
                        f = light ? (f | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR) : (f & ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
                    dv.setSystemUiVisibility(f);
                } catch (Exception ignored) { }
            });
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onPause() { super.onPause(); web.onPause(); }

    @Override
    protected void onResume() { super.onResume(); web.onResume(); }
}
