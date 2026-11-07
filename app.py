if st.session_state.signal_active_snp:
    if mercato_tipo == "🚀 Scanner Globale":
        st.success("Scanner completato!")
        st.markdown("### 🎯 VALUTE CON SEGNALE ATTIVO")
        if len(st.session_state.scanner_results) > 0:
            for res in st.session_state.scanner_results:
                dir_class = "signal-buy" if "BUY" in res['direction'] else "signal-sell"
                box_html = (
                    '<div class="analysis-box">'
                    '<h4 style="color:#ffffff;">' + res['asset'] + ' &rarr; <span class="' + dir_class + '">' + res['direction'] + '</span></h4>'
                    '<p style="color:#ffffff;"><b>Timeframe:</b> <span style="color:#2ecc71;">' + res['timeframe'] + '</span> | '
                    '<b>Confidence:</b> <span style="color:#2ecc71;">' + res['confidence'] + '</span> | '
                    '<b>RSI:</b> ' + res['rsi'] + ' | '
                    '<b>Entry:</b> <span style="color:#2ecc71;">' + res['entry_time'] + '</span></p>'
                    '</div>'
                )
                st.markdown(box_html, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="standby-box" style="border: 2px solid #ff4444; text-align: center;">'
                '<h4 style="color: #ff4444;">🛑 NESSUN SEGNALE IN QUESTO MOMENTO</h4>'
                '<p style="color:#ffffff;">Nessun asset soddisfa i filtri di allineamento Macro-Trend e ADX.</p>'
                '</div>',
                unsafe_allow_html=True
            )
    else:
        st.success("Analysis complete!")
        st.markdown("### SIGNAL RESULT")
        dir_display = st.session_state.cached_direction_snp
        dir_class = "signal-buy" if "BUY" in dir_display else ("signal-sell" if "SELL" in dir_display else "signal-standby")
        conf_display = st.session_state.cached_win_rate_snp
        conf_html = "<span style='color: #2ecc71; font-weight: bold;'>" + conf_display + "</span>" if conf_display != "N/A" else "N/A"
        status_display = st.session_state.cached_confidence_snp
        status_html = "<span style='color: #2ecc71; font-weight: bold;'>" + status_display + "</span>" if status_display == "Confluence Verified" else status_display

        result_html = (
            '<div class="analysis-box">'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Asset:</b> ' + str(st.session_state.cached_asset_display_snp) + '</p>'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Timeframe:</b> <span style="color:#2ecc71;">' + str(st.session_state.cached_tf_choice_snp) + '</span></p>'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Signal Direction:</b> <span class="' + dir_class + '">' + str(dir_display) + '</span></p>'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Entry Time (Candle Close):</b> <span style="color:#2ecc71;">' + str(st.session_state.cached_time_snp) + '</span></p>'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Dynamic AI Confidence:</b> ' + conf_html + '</p>'
            '<p style="color:#ffffff; margin: 6px 0;"><b>Filter Status:</b> ' + status_html + '</p>'
            '</div>'
        )
        st.markdown(result_html, unsafe_allow_html=True)

        details = st.session_state.cached_details_snp
        if details:
            if "STAND BY" in st.session_state.cached_direction_snp:
                standby_detail_html = (
                    '<div class="standby-box">'
                    '<h4 style="color: #ff4444; margin-top: 0;">🛑 STAND BY: FILTRI NON SUPERATI</h4>'
                    '<p style="color:#ffffff; margin-bottom: 10px;"><b>Asset:</b> ' + str(st.session_state.cached_asset_display_snp) + ' | <b>Timeframe:</b> ' + str(st.session_state.cached_tf_choice_snp) + '</p>'
                    '<hr style="border-color: #333333; margin: 10px 0;">'
                    '<p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Motivo:</b> Mercato laterale o disallineamento</p>'
                    '<p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>RSI:</b> ' + str(details.get("RSI", "N/A")) + '</p>'
                    '<p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Trend Macro:</b> ' + str(details.get("Trend Macro", "N/A")) + '</p>'
                    '<p style="color: #ffffff; text-align: left; margin: 5px 0;"><b>Forza ADX:</b> ' + str(details.get("ADX Strength", "N/A")) + '</p>'
                    '</div>'
                )
                st.markdown(standby_detail_html, unsafe_allow_html=True)
            else:
                bollinger_val = details.get('Bollinger Position', 'N/A')
                bollinger_html = "<span style='color: #2ecc71; font-weight: bold;'>" + bollinger_val + "</span>" if "Touch" in bollinger_val else bollinger_val
                
                v_rsi = str(details.get("RSI", "N/A"))
                v_macro = str(details.get("Trend Macro", "N/A"))
                v_adx = str(details.get("ADX Strength", "N/A"))
                
                box_head = '<h4>🎯 CONFLUENZA ISTITUZIONALE VERIFICATA</h4>'
                p_rsi = '<p style="color:#ffffff;"><b>RSI (14):</b> <span style="color:#2ecc71;">' + v_rsi + '</span></p>'
                p_macro = '<p style="color:#ffffff;"><b>Trend Macro:</b> ' + v_macro + '</p>'
                p_adx = '<p style="color:#ffffff;"><b>Forza ADX:</b> <span style="color:#2ecc71;">' + v_adx + '</span></p>'
                p_boll = '<p style="color:#ffffff;"><b>Posizione Bollinger:</b> ' + bollinger_html + '</p>'
                
                verified_html = '<div class="analysis-box">' + box_head + p_rsi + p_macro + p_adx + p_boll + '</div>'
                st.markdown(verified_html, unsafe_allow_html=True)

        st.markdown("### ⏳ Current Candle Countdown (Pocket Option Sync)")
        initial_left = get_seconds_to_next_candle(st.session_state.cached_tf_seconds_snp)
        
        timer_html = (
            '<div style="font-size: 28px; font-weight: bold; color: #2ecc71; text-align: center; background-color: #141414; padding: 15px; border-radius: 8px; border: 2px solid #2ecc71;" id="countdown_snp">Loading timer...</div>'
            '<script>'
            'var timeLeftSnp = ' + str(initial_left) + ';'
            'function updateTimerSnp() {'
            '    if (timeLeftSnp <= 0) {'
            '        document.getElementById("countdown_snp").innerHTML = "⏰ CANDELA CHIUSA!";'
            '        document.getElementById("countdown_snp").style.color = "#ff4444";'
            '        return;'
            '    }'
            '    var m = Math.floor(timeLeftSnp / 60);'
            '    var s = timeLeftSnp % 60;'
            '    document.getElementById("countdown_snp").innerHTML = "⏱️ " + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);'
            '    timeLeftSnp--;'
            '}'
            'setInterval(updateTimerSnp, 1000);'
            'updateTimerSnp();'
            '</script>'
        )
        components.html(timer_html, height=80)
  