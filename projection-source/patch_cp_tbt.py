"""Port basic CarPlay HUD behavior from HMG_Phone_Projection_TBT (AGPL-3.0)."""

def patch_cp_tbt(dipo, once):
    # Reference: ch0iiih/HMG_Phone_Projection_TBT @ daeaf32, CpTurns and Dipo.
    path = dipo / 'CpTurns.java'
    text = path.read_text(encoding='utf-8')
    text = once(text, '''                else m.put(index, new Maneuver(index, id, msg));
            }
            return;''', '''                else m.put(index, new Maneuver(index, id, msg));
                redrawManeuver(id, index);
            }
            return;''')
    text = once(text, '''                maneuvers.put(id, m);
            }
        }
    }''', '''                maneuvers.put(id, m);
            }
            redrawManeuver(id, index);
        }
    }

    private void redrawManeuver(int id, int index) {
        Update route = updates.get(id);
        if (route == null || route.state <= 0 || route.list == null) return;
        for (int listed : route.list) {
            if (listed == index) {
                turn(id, route);
                return;
            }
        }
    }''')
    text = once(text, '    String source;', '    String source;\n    boolean firstTurnSent;')
    text = once(text, '''        source = null;
    }''', '''        source = null;
        firstTurnSent = false;
    }''')
    text = once(text, '''        hudBlank();
    }

    /** forget every component''', '''        // A late maneuver must not repaint an explicitly stopped route.
        reset();
        hudBlank();
    }

    /** forget every component''')
    text = once(text, '''        if (id < 0 || u == null) return;
        if (u.state == 0) {
            stop();
            return;
        }
        int[] list = u.list == null ? null : u.list.clone();
        float dist = 0f;''', '''        if (id < 0 || u == null || u.state < 0) return;
        if (u.state == 0) {
            maneuvers.remove(id);
            u.clear();
            hudBlank();
            return;
        }
        int[] list = u.list;
        float dist = Float.NaN;''')
    text = once(text, '''                if (Float.isNaN(dist) || Float.isInfinite(dist)) dist = 0f;
            } catch (NumberFormatException e) {
                dist = 0f;''', '''                if (Float.isInfinite(dist) || dist < 0f) dist = Float.NaN;
            } catch (NumberFormatException e) {
                dist = Float.NaN;''')
    text = once(text, '        if (m == null || list == null) return;',
                '        if (m == null || list == null || list.length == 0) return;')
    text = once(text, '''        int icon = icon(x.type, x.side, x.junction, x.exit, u.state);
        // StartRoute has no direction: clear the previous app's HUD arrow.''', '''        int meters = u.distNext >= 0 ? u.distNext : x.distance;
        if (Float.isNaN(dist)) {
            if (meters < 0) return;
            dist = meters;
            unit = Cluster.UNIT_M;
        }
        int icon = icon(x.type, x.side, x.junction, x.exit, u.state);
        // StartRoute has no direction: clear the previous app's HUD arrow.''')
    text = once(text, '''        cluster.crossroadName(x.afterRoad);
        if (icon == 0) return;
        int type = icon, dir = 0, bar = 0;
        if (standardTurns) {
            // the phone's distance to this maneuver in meters (item 10), once it has sent one
            int meters = u.nextStr == null || u.nextStr.equals("") ? -1 : u.distNext;''',
                '''        if (icon == 0) return;
        int type = icon, bar = 0;
        float dir = direction(icon, x.hasExit, x.exit);
        if (standardTurns) {''')
    text = once(text, '''        cluster.tbtInfo(type, 0, dir, dist, 0, 0, unit, bar, 0);
        sendHud(icon, id, u);
        sendHudDist(dist, unit);''', '''        cluster.tbtInfo(type, 0, dir, dist, 0, 0, unit, bar, 0);
        // Some clusters accept the road name only after a valid turn frame.
        cluster.crossroadName(x.afterRoad);
        sendHud(icon, id, u);
        sendHudDist(dist, unit);
        if (!firstTurnSent) {
            firstTurnSent = true;
            Dipo.log("CarPlay: first HUD turn submitted");
        }''')
    text = once(text, '''    /**
     * The cluster icon for a maneuver:''',
                '''    static float direction(int icon, boolean hasExit, int exit) {
        if (hasExit && exit >= -180 && exit <= 180) return (exit + 360) % 360;
        switch (icon) {
            case 66: return 30;
            case 67: return 90;
            case 68: return 135;
            case 69: return 225;
            case 70: return 270;
            case 71: return 330;
            case 72:
            case 73: return 180;
            default: return 0;
        }
    }

    /**
     * The cluster icon for a maneuver:''')
    text = once(text, '''            state = 0;
            maneuverState = 1;''', '''            state = -1;
            maneuverState = 1;''')
    text = once(text, '            distNext = 0;', '            distNext = -1;')
    text = once(text, '''            Iap2NotiMsg.Iap2ObjGroup g = msg == null ? null : msg.getItemGroup();
            if (g == null) return;
            for''', '''            Iap2NotiMsg.Iap2ObjGroup g = msg == null ? null : msg.getItemGroup();
            if (g == null) return;
            int previousManeuver = list == null || list.length == 0 ? -1 : list[0];
            boolean gotNumericDistance = false, gotDisplayDistance = false;
            for''')
    text = once(text, '                        else if (item == 10) distNext = v[0];',
                '                        else if (item == 10 && v.length > 0) { distNext = v[0]; gotNumericDistance = true; }')
    text = once(text, '                            case 11: nextStr = v[0]; break;',
                '                            case 11: nextStr = v[0]; gotDisplayDistance = true; break;')
    text = once(text, '''            }
        }
    }

    /** one maneuver (DiPO e/v) */''', '''            }
            int currentManeuver = list == null || list.length == 0 ? -1 : list[0];
            if (previousManeuver >= 0 && previousManeuver != currentManeuver) {
                if (!gotNumericDistance) distNext = -1;
                if (!gotDisplayDistance) nextStr = "";
            }
        }
    }

    /** one maneuver (DiPO e/v) */''')
    text = once(text, '''                                    list = new int[n];
                                    for (int j = 0; j < n; j++) list[j] = v[j];''',
                '''                                    list = java.util.Arrays.copyOf(v, Math.min(n, v.length));''')
    text = once(text, '        int[] angles;\n\n        Maneuver', '        int[] angles;\n        boolean hasExit;\n\n        Maneuver')
    text = once(text, '            distance = 0;', '            distance = -1;')
    text = once(text, '''            this.index = index;
            exit = 0;
            for''', '''            this.index = index;
            if (g == null) return;
            for''')
    text = once(text, '''                        } else if (item == 11 && v != null) {
                            exit = v[0];''', '''                        } else if (item == 11 && v != null && v.length > 0) {
                            exit = v[0];
                            hasExit = true;''')
    text = once(text, "        /** as DiPO, the exit angle resets with every update (it's only kept if this one carries it) */",
                "        /** Partial maneuver updates retain an exit angle that was already received. */")
    path.write_text(text, encoding='utf-8', newline='\n')

    path = dipo / 'RgWatch.java'
    text = path.read_text(encoding='utf-8')
    text = once(text, "session, route guidance (Stop, 200 ms,\n *    Start) and Now Playing",
                "session, route guidance (Start) and Now Playing")
    text = once(text, 'route guidance (Stop, Start) and Now Playing asked again', 'route guidance (Start) and Now Playing asked again')
    path.write_text(text, encoding='utf-8', newline='\n')

    path = dipo / 'Dipo.java'
    text = path.read_text(encoding='utf-8')
    text = once(text, '''                    restartRouteGuidance();
                }
            });
        }
        if (nowPlaying && npHandler != null)''', '''                    IIap2Service service = iap2;
                    RgWatch watch = rgWatch;
                    if (service == null || (watch != null && !watch.linkReady())) return;
                    try {
                        log("CarPlay: route guidance Start-only result="
                                + service.Iap2SvcStartRouteGuidanceUpdate(RG_COMPONENTS, true, true));
                    } catch (Exception e) {
                        error("CarPlay route guidance Start-only", e);
                    }
                }
            });
        }
        if (nowPlaying && npHandler != null)''')
    text = once(text, 'phone is\n     * asked for route guidance (Stop, then Start, as a source change does) and Now Playing again.',
                'phone is\n     * asked to start route guidance and send Now Playing again.')
    path.write_text(text, encoding='utf-8', newline='\n')
