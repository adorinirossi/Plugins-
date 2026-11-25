// Three Minds Publishing — gerador de título animado para After Effects (ExtendScript)
// Uso: After Effects > Arquivo > Scripts > Executar arquivo de script...
// Edite as variáveis abaixo antes de executar.

var TITULO     = "TÍTULO DO LIVRO";
var SUBTITULO  = "Autora · Em breve";
var FONTE      = "Arial-BoldMT";      // nome PostScript da fonte ativa (Adobe Fonts)
var FONTE_SUB  = "ArialMT";
var COR        = [1, 1, 1];           // RGB 0–1 (ex.: #B3122E = [0.70, 0.07, 0.18])
var COR_FUNDO  = null;                // ex.: [0.05, 0.02, 0.03] ou null para transparente
var FORMATO    = "9:16";              // "9:16", "16:9", "4:5", "1:1"
var DURACAO    = 5;                   // segundos (mínimo 2)
var FPS        = 30;
var LARGURA_MAX = 0.84;               // fração da largura do quadro que o texto pode ocupar (zona segura)

// Novelinha vertical: preencha para gerar uma composição por episódio, com SUBTITULO = "EP. NN — título".
// Ex.: var EPISODIOS = ["O contrato", "A primeira noite", "O segredo"];  var EP_INICIAL = 1;
var EPISODIOS  = [];
var EP_INICIAL = 1;

(function () {
    var dims = { "9:16": [1080, 1920], "16:9": [1920, 1080], "4:5": [1080, 1350], "1:1": [1080, 1080] }[FORMATO];
    if (!dims) { alert("FORMATO inválido: use 9:16, 16:9, 4:5 ou 1:1"); return; }
    if (DURACAO < 2) { alert("DURACAO deve ser de pelo menos 2 segundos"); return; }
    var cx = dims[0] / 2, cy = dims[1] / 2;
    var limite = dims[0] * LARGURA_MAX;

    function pad2(n) { return (n < 10 ? "0" : "") + n; }

    function texto(comp, conteudo, fonte, tamanho, y, nome) {
        var layer = comp.layers.addText(conteudo);
        layer.name = nome;
        var prop = layer.property("Source Text");
        var doc = prop.value;
        doc.font = fonte; doc.fontSize = tamanho; doc.fillColor = COR;
        doc.applyFill = true; doc.applyStroke = false;
        doc.justification = ParagraphJustification.CENTER_JUSTIFY;
        prop.setValue(doc);
        // Encolhe a fonte até o texto caber na zona segura (títulos longos estouravam a tela).
        var guarda = 0;
        while (layer.sourceRectAtTime(0, false).width > limite && guarda < 40) {
            doc = prop.value; doc.fontSize = doc.fontSize * 0.94; prop.setValue(doc); guarda++;
        }
        if (doc.font !== fonte) {
            $.writeln("Aviso: fonte '" + fonte + "' não está ativa; o After Effects usou '" + doc.font + "'.");
        }
        // Centraliza pelo retângulo real do texto (independe do tamanho final da fonte).
        var r = layer.sourceRectAtTime(0, false);
        layer.property("Transform").property("Anchor Point").setValue([r.left + r.width / 2, r.top + r.height / 2]);
        layer.property("Transform").property("Position").setValue([cx, y]);
        return layer;
    }

    function animar(layer, atraso, yFinal) {
        var tr = layer.property("Transform");
        var op = tr.property("Opacity"), pos = tr.property("Position"), sc = tr.property("Scale");
        var entrada = Math.min(0.8, DURACAO / 4), saida = Math.min(0.6, DURACAO / 5);
        var t0 = Math.min(atraso, DURACAO / 4), t1 = t0 + entrada, s0 = DURACAO - saida, s1 = DURACAO;
        if (t1 >= s0) { t1 = s0 - 0.05; }
        op.setValueAtTime(t0, 0); op.setValueAtTime(t1, 100); op.setValueAtTime(s0, 100); op.setValueAtTime(s1, 0);
        pos.setValueAtTime(t0, [cx, yFinal + 60]); pos.setValueAtTime(t1, [cx, yFinal]);
        sc.setValueAtTime(t0, [96, 96]); sc.setValueAtTime(DURACAO, [104, 104]);
        var ease = new KeyframeEase(0, 75);
        for (var i = 1; i <= pos.numKeys; i++) { pos.setTemporalEaseAtKey(i, [ease], [ease]); }
        for (var j = 1; j <= op.numKeys; j++) { op.setTemporalEaseAtKey(j, [ease], [ease]); }
    }

    function criar(nomeComp, titulo, subtitulo) {
        var comp = app.project.items.addComp(nomeComp, dims[0], dims[1], 1, DURACAO, FPS);
        if (COR_FUNDO) { comp.layers.addSolid(COR_FUNDO, "Fundo", dims[0], dims[1], 1, DURACAO); }
        var tamTitulo = Math.round(dims[0] * 0.09);
        var yT = cy - tamTitulo * 0.3, yS = cy + tamTitulo * 0.9;
        var t = texto(comp, titulo, FONTE, tamTitulo, yT, "Título");
        animar(t, 0.2, yT);
        if (subtitulo) {
            var s = texto(comp, subtitulo, FONTE_SUB, Math.round(tamTitulo * 0.38), yS, "Subtítulo");
            animar(s, 0.6, yS);
        }
        return comp;
    }

    app.beginUndoGroup("Título Three Minds");
    var base = "TM_TITULO_" + FORMATO.replace(":", "x");
    var ultima;
    if (EPISODIOS.length) {
        for (var e = 0; e < EPISODIOS.length; e++) {
            var n = pad2(EP_INICIAL + e);
            ultima = criar(base + "_EP" + n, TITULO, "EP. " + n + " — " + EPISODIOS[e]);
        }
    } else {
        ultima = criar(base, TITULO, SUBTITULO);
    }
    ultima.openInViewer();
    app.endUndoGroup();
})();
