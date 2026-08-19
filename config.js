// Configuração do site. Único arquivo que muda entre "só divulgar" e "vender de verdade".
window.CESP = {

  // Deixe VAZIO enquanto o backend não estiver no ar.
  // Vazio  -> o pedido é fechado pelo WhatsApp.
  // Preenchido -> o carrinho vai para o checkout do Worker.
  API_BASE: "https://cesp-api.cesp.workers.dev",

  // Número no formato internacional, só dígitos. Ex.: 5516999999999
  WHATSAPP: "5516994476177",

  INSTAGRAM: "https://instagram.com/collectorseditionsp",
  EMAIL: "collectorseditionsp@gmail.com",
  SITE_URL: "https://www.collectorsedition.club",

  // Apoiar o projeto. Deixe "" no que você não usa — some do site sozinho.
  // Brasil primeiro para quem navega em português, exterior primeiro em inglês.
  APOIO: {
    PIX:    "",   // chave Pix: e-mail, telefone, CPF ou aleatória
    PIX_NOME: "", // nome que aparece para quem paga
    PAYPAL: "",   // https://paypal.me/SEU_USUARIO
    VENMO:  "",   // @seu-usuario
    ZELLE:  ""    // e-mail ou telefone cadastrado
  }
};
