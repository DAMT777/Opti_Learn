export default {
  logo: <span style={{ fontWeight: 'bold' }}>OptiLearn Web - Manual de Usuario</span>,
  project: {
    link: 'https://github.com/DAMT777/Programacion_No_Lineal'
  },
  docsRepositoryBase: 'https://github.com/DAMT777/Programacion_No_Lineal',
  footer: {
    text: 'Manual de Usuario OptiLearn Web © 2025 - Universidad de los Llanos'
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – OptiLearn Web'
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="OptiLearn Web - Manual de Usuario" />
      <meta property="og:description" content="Guía completa para usar el sistema de optimización no lineal" />
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossOrigin="anonymous" />
    </>
  )
}
