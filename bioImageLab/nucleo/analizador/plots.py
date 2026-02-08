def plot_bioImagen_jn(self, canal: int = 0, z_stack: int = 0, timelapse: int = 0, fluoroforo: str = None):
        """
          Visualización avanzada de BioImágenes con estilos Retro (fluoróforos) o Profesional (Trans).

          Argumentos:
              canal: Canal a visualizar (default: 0)
              z_stack: Índice del z-stack (default: 0)
              timelapse: Índice del timelapse (default: 0)
              fluoroforo: Tipo de fluoróforo ('gfp', 'rfp', 'yfp', 'mcherry', 'dsred',
                        'cerulean_venus', 'cy5', 'dapi', 'fitc', 'mng').
                        Si es None, usa estilo Profesional (Trans).

          Retorna:
              None si hay error

          Complejidad:
              O(1) - solo extrae y muestra slices específicos
        """
        if self.img is None:
            print("Error: Primero debes cargar la imagen con leer_bioImagen()")
            return None

        try:
            T, Z, C, Y, X = self.forma

            # Validación de índices
            if canal >= C or canal < 0:
                print(f"Error: Canal {canal} no existe. Disponibles: 0-{C-1}")
                print(f"Nombres de canales: {self.canales}")
                return None
            if timelapse >= T or z_stack >= Z:
                print(f"Error: Índices fuera de rango. T max: {T-1}, Z max: {Z-1}")
                return None

            # Extraer corte de imagen original
            corte_imagen = self.img[timelapse, z_stack, canal, :, :]

            # --- MAPA DE COLORES PARA FLUORÓFOROS (RETRO) ---
            mapa_fluoroforos = {
                'gfp': 'Greens', 'fitc': 'Greens', 'mng': 'Greens',
                'rfp': 'Reds', 'mcherry': 'Reds', 'dsred': 'Reds',
                'yfp': 'YlOrBr',  # Amarillo brillante
                'dapi': 'Blues', 'cerulean_venus': 'GnBu',
                'cy5': 'Purples'
            }

            # Determinar estilo
            es_retro = False
            target_cmap = 'magma'  # Por defecto para modo Profesional

            if fluoroforo and fluoroforo.lower() in mapa_fluoroforos:
                target_cmap = mapa_fluoroforos[fluoroforo.lower()]
                es_retro = True

            # Verificar si hay imagen binarizada
            tiene_binaria = (self.img_normalizada is not None and
                            self.img_binaria is not None and
                            canal < len(self.img_binaria) and
                            self.img_binaria[canal] is not None)

            # --- CONFIGURACIÓN DE ESTILO ---
            accent_color = '#33FF33' if es_retro else 'white'
            face_color = 'black' if es_retro else '#0a0a0a'
            font_style = 'monospace' if es_retro else 'sans-serif'

            # Crear figura con contexto de estilo
            plt.style.use('dark_background')
            num_plots = 2 if tiene_binaria else 1
            fig, axes = plt.subplots(1, num_plots,
                                    figsize=(15 if tiene_binaria else 8, 7),
                                    facecolor=face_color)

            # Convertir axes a lista si solo hay un plot
            if not tiene_binaria:
                axes = [axes]

            # --- PLOT 1: IMAGEN ORIGINAL ---
            if es_retro:
                # Invertir la imagen: fondo oscuro → negro, señales altas → blancas
                corte_invertido = corte_imagen.max() - corte_imagen
                # Aplicar colormap del fluoróforo (ahora sobre imagen invertida)
                cmap = plt.colormaps.get_cmap(target_cmap).copy()
                im0 = axes[0].imshow(corte_invertido, cmap=cmap, interpolation='bilinear')
                axes[0].set_facecolor('black')  # Fondo negro
            else:
                im0 = axes[0].imshow(corte_imagen, cmap=target_cmap)

            if es_retro:
                titulo_0 = f">> {fluoroforo.upper()}_SIGNAL"
                axes[0].set_title(titulo_0, color=accent_color, fontsize=12,
                                loc='left', pad=15, fontfamily='monospace')
                axes[0].grid(color=accent_color, linestyle=':', alpha=0.3)
                for spine in axes[0].spines.values():
                    spine.set_color(accent_color)
                    spine.set_linewidth(1.5)
                axes[0].tick_params(colors=accent_color, labelsize=8)
            else:
                titulo_0 = f"Canal: {self.canales[canal]}"
                axes[0].set_title(titulo_0, color=accent_color, fontsize=12, pad=15)
                axes[0].axis('off')
                plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04,
                        label='Intensidad')

            # --- PLOT 2: IMAGEN BINARIA (si existe) ---
            if tiene_binaria:
                corte_bin = self.img_binaria[canal][timelapse, z_stack, 0, :, :]

                if es_retro:
                    # En modo retro: invertir binaria y aplicar color del fluoróforo
                    # 0 → 255 (blanco→color), 255 → 0 (negro)
                    corte_bin_invertido = 255 - corte_bin
                    cmap_bin = plt.colormaps.get_cmap(target_cmap).copy()
                    axes[1].imshow(corte_bin_invertido, cmap=cmap_bin, interpolation='nearest')
                    axes[1].set_facecolor('black')  # Fondo negro
                else:
                    # En modo Trans: objetos blancos sobre fondo negro
                    axes[1].imshow(corte_bin, cmap='gray_r')
                    axes[1].set_facecolor('black')

                if es_retro:
                    axes[1].set_title(">> BINARY_DECODE", color=accent_color,
                                    fontsize=12, loc='left', pad=15,
                                    fontfamily='monospace')
                    axes[1].grid(color=accent_color, linestyle=':', alpha=0.3)
                    for spine in axes[1].spines.values():
                        spine.set_color(accent_color)
                        spine.set_linewidth(1.5)
                    axes[1].tick_params(colors=accent_color, labelsize=8)
                else:
                    axes[1].set_title("Binaria", color=accent_color,
                                    fontsize=12, pad=15)
                    axes[1].axis('off')

            # Título superior
            suptitle_text = f"Z:{z_stack} | T:{timelapse} | BIO-IMAGING SYSTEM" if es_retro else f"Canal {canal} | Z-stack:{z_stack} | Tiempo:{timelapse}"
            plt.suptitle(suptitle_text, color=accent_color, fontsize=10,
                        alpha=0.7, y=0.98, fontfamily=font_style)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error al graficar la imagen: {e}")
            import traceback
            traceback.print_exc()
            return None