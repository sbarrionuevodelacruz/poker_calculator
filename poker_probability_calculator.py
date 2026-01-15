"""
Calculadora de Probabilidades de Poker
Aplicación para calcular las probabilidades de ganar según las cartas propias
y las cartas comunitarias que van saliendo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
from collections import Counter
from typing import List, Tuple, Optional
from collections import Counter
import threading
import json
import os
import os

class PokerHandEvaluator:
    """Evalúa y compara manos de poker"""
    
    # Rankings de manos (mayor número = mejor mano)
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10
    
    @staticmethod
    def get_card_value(card: str) -> int:
        """Convierte una carta a su valor numérico"""
        rank = card[0]
        if rank == 'A':
            return 14
        elif rank == 'K':
            return 13
        elif rank == 'Q':
            return 12
        elif rank == 'J':
            return 11
        elif rank == 'T':
            return 10
        else:
            return int(rank)
    
    @staticmethod
    def get_card_suit(card: str) -> str:
        """Obtiene el palo de una carta"""
        return card[1]
    
    @staticmethod
    def evaluate_hand(cards: List[str]) -> Tuple[int, List[int]]:
        """
        Evalúa una mano de 5-7 cartas y retorna (rank, kickers)
        rank: tipo de mano (1-10)
        kickers: valores ordenados para desempate
        """
        if len(cards) < 5:
            return (0, [])
        
        # Convertir cartas a valores y palos
        values = [PokerHandEvaluator.get_card_value(c) for c in cards]
        suits = [PokerHandEvaluator.get_card_suit(c) for c in cards]
        
        # Contar valores y palos
        value_counts = Counter(values)
        suit_counts = Counter(suits)
        
        # Ordenar valores por frecuencia y luego por valor
        sorted_values = sorted(value_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        values_desc = sorted(values, reverse=True)
        
        # Verificar flush
        is_flush = max(suit_counts.values()) >= 5
        flush_suit = None
        if is_flush:
            for suit, count in suit_counts.items():
                if count >= 5:
                    flush_suit = suit
                    break
        
        # Verificar straight
        unique_values = sorted(set(values))
        is_straight = False
        straight_high = 0
        
        # Verificar straight normal
        for i in range(len(unique_values) - 4):
            if unique_values[i+4] - unique_values[i] == 4:
                is_straight = True
                straight_high = unique_values[i+4]
                break
        
        # Verificar straight con A-2-3-4-5 (wheel)
        if 14 in unique_values and 2 in unique_values and 3 in unique_values and 4 in unique_values and 5 in unique_values:
            is_straight = True
            straight_high = 5
        
        # Evaluar tipo de mano
        counts = sorted(value_counts.values(), reverse=True)
        
        # Royal Flush o Straight Flush
        if is_flush and is_straight:
            if straight_high == 14:
                return (PokerHandEvaluator.ROYAL_FLUSH, [14])
            else:
                return (PokerHandEvaluator.STRAIGHT_FLUSH, [straight_high])
        
        # Four of a Kind
        if counts[0] == 4:
            four_kind = sorted_values[0][0]
            kicker = sorted_values[1][0] if len(sorted_values) > 1 else 0
            return (PokerHandEvaluator.FOUR_OF_A_KIND, [four_kind, kicker])
        
        # Full House
        if counts[0] == 3 and len(counts) > 1 and counts[1] >= 2:
            three_kind = sorted_values[0][0]
            pair = sorted_values[1][0]
            return (PokerHandEvaluator.FULL_HOUSE, [three_kind, pair])
        
        # Flush
        if is_flush:
            flush_cards = [v for v, s in zip(values, suits) if s == flush_suit]
            flush_cards.sort(reverse=True)
            return (PokerHandEvaluator.FLUSH, flush_cards[:5])
        
        # Straight
        if is_straight:
            return (PokerHandEvaluator.STRAIGHT, [straight_high])
        
        # Three of a Kind
        if counts[0] == 3:
            three_kind = sorted_values[0][0]
            kickers = [v for v in values_desc if v != three_kind][:2]
            return (PokerHandEvaluator.THREE_OF_A_KIND, [three_kind] + kickers)
        
        # Two Pair
        if counts[0] == 2 and len(counts) > 1 and counts[1] == 2:
            pairs = [sorted_values[0][0], sorted_values[1][0]]
            pairs.sort(reverse=True)
            kicker = [v for v in values_desc if v not in pairs][0]
            return (PokerHandEvaluator.TWO_PAIR, pairs + [kicker])
        
        # Pair
        if counts[0] == 2:
            pair = sorted_values[0][0]
            kickers = [v for v in values_desc if v != pair][:3]
            return (PokerHandEvaluator.PAIR, [pair] + kickers)
        
        # High Card
        return (PokerHandEvaluator.HIGH_CARD, values_desc[:5])
    
    @staticmethod
    def compare_hands(hand1: Tuple[int, List[int]], hand2: Tuple[int, List[int]]) -> int:
        """Compara dos manos. Retorna 1 si hand1 gana, -1 si hand2 gana, 0 si empate"""
        rank1, kickers1 = hand1
        rank2, kickers2 = hand2
        
        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            # Comparar kickers
            for k1, k2 in zip(kickers1, kickers2):
                if k1 > k2:
                    return 1
                elif k1 < k2:
                    return -1
            return 0


class ProbabilityCalculator:
    """Calcula probabilidades usando simulación Monte Carlo"""
    
    def __init__(self):
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']  # Usar 'T' en lugar de '10'
        self.suits = ['♠', '♥', '♦', '♣']
        self.all_cards = [rank + suit for rank in self.ranks for suit in self.suits]
        # Pre-calcular set para búsqueda más rápida
        self.all_cards_set = set(self.all_cards)
    
    def get_available_cards(self, known_cards: List[str]) -> List[str]:
        """Retorna las cartas disponibles (no conocidas) - optimizado"""
        # Normalizar las cartas conocidas para comparación (10 -> T)
        normalized_known = set()
        for card in known_cards:
            if card.startswith('10'):
                normalized_known.add('T' + card[2:])
            else:
                normalized_known.add(card)
        
        # Filtrar cartas disponibles
        return [card for card in self.all_cards if card not in normalized_known]
    
    def calculate_win_probability(self, 
                                 my_cards: List[str], 
                                 community_cards: List[str],
                                 num_players: int,
                                 simulations: int = 20000) -> Tuple[float, List[Tuple[str, int]]]:
        """
        Calcula la probabilidad de ganar usando simulación Monte Carlo
        Retorna: (probabilidad, lista de (mano_ganadora, frecuencia))
        """
        if len(my_cards) < 2:
            return (0.0, [])
        
        known_cards = my_cards + community_cards
        wins = 0
        losing_hands = Counter()  # Contador de manos que me ganan
        
        hand_names = {
            1: "Carta Alta", 2: "Par", 3: "Doble Par", 4: "Trío",
            5: "Escalera", 6: "Color", 7: "Full House", 8: "Poker",
            9: "Escalera de Color", 10: "Escalera Real"
        }
        
        # Pre-calcular cartas disponibles una sola vez
        available_cards = self.get_available_cards(known_cards)
        total_needed = (num_players - 1) * 2 + (5 - len(community_cards))
        
        for _ in range(simulations):
            # Crear copia del mazo y barajar
            deck = available_cards.copy()
            random.shuffle(deck)
            
            # Verificar que tenemos suficientes cartas
            if len(deck) < total_needed:
                # Si no hay suficientes cartas, saltar esta simulación
                continue
            
            # Repartir cartas a los otros jugadores (más eficiente)
            other_players_cards = []
            deck_index = 0
            
            for _ in range(num_players - 1):
                # Cada jugador necesita 2 cartas
                player_cards = [deck[deck_index], deck[deck_index + 1]]
                deck_index += 2
                other_players_cards.append(player_cards)
            
            # Completar las cartas comunitarias si faltan
            needed_community = 5 - len(community_cards)
            remaining_community = deck[deck_index:deck_index + needed_community]
            all_community = community_cards + remaining_community
            
            # Evaluar mi mano
            my_hand = my_cards + all_community
            my_evaluation = PokerHandEvaluator.evaluate_hand(my_hand)
            
            # Evaluar manos de otros jugadores
            # Encontrar la mejor mano entre todos los oponentes
            best_opponent_evaluation = None
            best_opponent_rank = 0
            
            for other_cards in other_players_cards:
                other_hand = other_cards + all_community
                other_evaluation = PokerHandEvaluator.evaluate_hand(other_hand)
                other_rank, _ = other_evaluation
                
                # Encontrar la mejor mano del oponente
                if best_opponent_evaluation is None:
                    best_opponent_evaluation = other_evaluation
                    best_opponent_rank = other_rank
                else:
                    # Comparar con la mejor mano encontrada hasta ahora
                    comp = PokerHandEvaluator.compare_hands(best_opponent_evaluation, other_evaluation)
                    if comp < 0:  # Esta mano del oponente es mejor
                        best_opponent_evaluation = other_evaluation
                        best_opponent_rank = other_rank
            
            # Comparar mi mano con la mejor mano de todos los oponentes
            if best_opponent_evaluation is not None:
                comparison = PokerHandEvaluator.compare_hands(my_evaluation, best_opponent_evaluation)
                
                # Si la mejor mano del oponente es MEJOR que la mía, pierdo
                if comparison < 0:
                    best_opponent_hand = hand_names.get(best_opponent_rank, "Desconocido")
                    losing_hands[best_opponent_hand] += 1
                else:
                    # Gano o empato (comparison >= 0)
                    wins += 1
            else:
                # No hay oponentes (no debería pasar, pero por seguridad)
                wins += 1
        
        # Obtener las 3 manos más frecuentes que me ganan
        top_losing_hands = losing_hands.most_common(3)
        
        return (wins / simulations, top_losing_hands)


class PreflopStrategy:
    """Maneja la estrategia preflop y recomendaciones de apuestas"""
    
    def __init__(self):
        print("Cargando tabla de preflop...")
        self.preflop_table = self._load_preflop_table()
    
    def _load_preflop_table(self):
        """Carga la tabla de preflop desde archivo o usa una por defecto"""
        # Intentar cargar primero el nuevo formato, luego el antiguo
        table_file2 = "D:\\preflop_strategy2.json.txt"
        table_file = "D:\\preflop_strategy.json.txt"
        
        # Intentar cargar el nuevo formato (preflop_strategy2.json.txt)
        if os.path.exists(table_file2):
            try:
                print(f"Cargando tabla de preflop desde archivo: {table_file2}")
                with open(table_file2, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Verificar si es el formato nuevo
                    if 'metadata' in data or 'open_raise' in data:
                        print("Formato nuevo detectado - usando estrategia completa")
                        return data
            except Exception as e:
                print(f"Error al cargar la tabla de preflop: {table_file2} - {e}")
                pass
        
        # Intentar cargar el formato antiguo
        if os.path.exists(table_file):
            try:
                print(f"Cargando tabla de preflop desde archivo: {table_file}")
                with open(table_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Verificar si es el formato nuevo o antiguo
                    if 'metadata' in data or 'open_raise' in data:
                        print("Formato nuevo detectado - usando estrategia completa")
                        return data
                    else:
                        print("Formato antiguo detectado - usando conversión")
                        return data
            except Exception as e:
                print(f"Error al cargar la tabla de preflop: {table_file} - {e}")
                pass
        
        # Tabla por defecto (estrategia básica conservadora)
        print("Cargando tabla de preflop por defecto...")
        return self._get_default_preflop_table()
    
    def _get_default_preflop_table(self):
        """Tabla preflop por defecto - estrategia básica"""
        # Estructura: {mano: {posición: {num_players: acción}}}
        # Acciones: 'fold', 'call', 'raise', 'all-in', '3bet'
        
        # Manos premium - siempre raise
        premium_hands = ['AA', 'KK', 'QQ', 'AKs', 'AKo']
        # Manos fuertes - raise desde posiciones tempranas, call desde tardías
        strong_hands = ['JJ', 'TT', 'AQs', 'AQo', 'AJs', 'KQs']
        # Manos medias - call/raise según posición
        medium_hands = ['99', '88', 'ATs', 'KJs', 'QJs', 'JTs']
        # Manos especulativas - call desde posiciones tardías
        speculative_hands = ['77', '66', 'A9s', 'KTs', 'QTs', 'J9s', 'T9s', '98s']
        
        table = {}
        
        # Manos premium - siempre 3bet o all-in según situación
        # AA y KK: muy agresivo
        table['AA'] = {
            'early': {'2-3': 'all-in', '4-6': '3bet', '7-10': '3bet'},
            'middle': {'2-3': 'all-in', '4-6': '3bet', '7-10': '3bet'},
            'late': {'2-3': 'all-in', '4-6': 'all-in', '7-10': '3bet'}
        }
        table['KK'] = {
            'early': {'2-3': 'all-in', '4-6': '3bet', '7-10': '3bet'},
            'middle': {'2-3': 'all-in', '4-6': '3bet', '7-10': '3bet'},
            'late': {'2-3': 'all-in', '4-6': '3bet', '7-10': '3bet'}
        }
        # QQ y AK: agresivo pero no tanto
        table['QQ'] = {
            'early': {'2-3': '3bet', '4-6': '3bet', '7-10': 'raise'},
            'middle': {'2-3': '3bet', '4-6': '3bet', '7-10': 'raise'},
            'late': {'2-3': '3bet', '4-6': '3bet', '7-10': '3bet'}
        }
        table['AKs'] = {
            'early': {'2-3': '3bet', '4-6': 'raise', '7-10': 'raise'},
            'middle': {'2-3': '3bet', '4-6': '3bet', '7-10': 'raise'},
            'late': {'2-3': '3bet', '4-6': '3bet', '7-10': '3bet'}
        }
        table['AKo'] = {
            'early': {'2-3': '3bet', '4-6': 'raise', '7-10': 'raise'},
            'middle': {'2-3': '3bet', '4-6': 'raise', '7-10': 'raise'},
            'late': {'2-3': '3bet', '4-6': '3bet', '7-10': 'raise'}
        }
        
        # Manos fuertes
        for hand in strong_hands:
            table[hand] = {
                'early': {'2-3': 'raise', '4-6': 'call', '7-10': 'fold'},
                'middle': {'2-3': 'raise', '4-6': 'raise', '7-10': 'call'},
                'late': {'2-3': 'raise', '4-6': 'raise', '7-10': 'raise'}
            }
        
        # Manos medias
        for hand in medium_hands:
            table[hand] = {
                'early': {'2-3': 'call', '4-6': 'fold', '7-10': 'fold'},
                'middle': {'2-3': 'call', '4-6': 'call', '7-10': 'fold'},
                'late': {'2-3': 'raise', '4-6': 'call', '7-10': 'call'}
            }
        
        # Manos especulativas
        for hand in speculative_hands:
            table[hand] = {
                'early': {'2-3': 'fold', '4-6': 'fold', '7-10': 'fold'},
                'middle': {'2-3': 'call', '4-6': 'fold', '7-10': 'fold'},
                'late': {'2-3': 'call', '4-6': 'call', '7-10': 'call'}
            }
        
        return table
    
    def normalize_hand(self, card1: str, card2: str) -> str:
        """Normaliza una mano a formato de tabla (ej: 'AKs', 'AKo', 'AA')"""
        # Obtener valores
        def get_value(card):
            rank = card[0] if card[0] != 'T' else '10'
            if rank == '10':
                return 10
            elif rank == 'J':
                return 11
            elif rank == 'Q':
                return 12
            elif rank == 'K':
                return 13
            elif rank == 'A':
                return 14
            else:
                return int(rank)
        
        val1 = get_value(card1)
        val2 = get_value(card2)
        
        # Ordenar de mayor a menor
        if val1 < val2:
            val1, val2 = val2, val1
            card1, card2 = card2, card1
        
        # Determinar si es suited
        suited = card1[1] == card2[1]
        
        # Convertir a notación
        def val_to_rank(val):
            if val == 14:
                return 'A'
            elif val == 13:
                return 'K'
            elif val == 12:
                return 'Q'
            elif val == 11:
                return 'J'
            elif val == 10:
                return 'T'
            else:
                return str(val)
        
        rank1 = val_to_rank(val1)
        rank2 = val_to_rank(val2)
        
        # Si es par
        if val1 == val2:
            return rank1 + rank2
        
        # Si es suited u offsuit
        if suited:
            return rank1 + rank2 + 's'
        else:
            return rank1 + rank2 + 'o'
    
    def get_position(self, player_index: int, num_players: int, dealer_position: int = 0) -> str:
        """
        Determina la posición del jugador respecto al dealer
        Retorna posiciones del nuevo formato: 'EP', 'MP', 'CO', 'BTN', 'SB', 'BB'
        """
        # Calcular posición relativa al dealer
        # Orden de acción: BTN (dealer), SB, BB, UTG, UTG+1, MP, MP+1, CO
        position_relative = (player_index - dealer_position) % num_players
        
        # Determinar posición según número de jugadores
        if num_players <= 3:
            # Heads-up o 3 jugadores
            if position_relative == 0:
                return 'BTN'  # Button
            elif position_relative == 1:
                return 'SB'  # Small Blind
            else:
                return 'BB'  # Big Blind
        elif num_players <= 6:
            # 4-6 jugadores
            if position_relative == 0:
                return 'BTN'  # Button
            elif position_relative == 1:
                return 'SB'  # Small Blind
            elif position_relative == 2:
                return 'BB'  # Big Blind
            elif position_relative == num_players - 1:
                return 'CO'  # Cutoff
            elif position_relative == num_players - 2:
                return 'MP'  # Middle Position
            else:
                return 'EP'  # Early Position (UTG)
        else:
            # 7-10 jugadores
            if position_relative == 0:
                return 'BTN'  # Button
            elif position_relative == 1:
                return 'SB'  # Small Blind
            elif position_relative == 2:
                return 'BB'  # Big Blind
            elif position_relative == num_players - 1:
                return 'CO'  # Cutoff
            elif position_relative >= num_players - 3:
                return 'MP'  # Middle Position
            else:
                return 'EP'  # Early Position (UTG, UTG+1, etc.)
    
    def get_recommendation(self, card1: str, card2: str, position: str, num_players: int, 
                          has_raise: bool = False, num_raises: int = 0) -> str:
        """
        Obtiene la recomendación de apuesta para una mano preflop
        Usa el nuevo formato JSON con todas las situaciones específicas
        """
        if len(card1) < 2 or len(card2) < 2:
            return 'fold'
        
        # Normalizar mano
        hand = self.normalize_hand(card1, card2)
        
        # Verificar si estamos usando el formato nuevo o antiguo
        is_new_format = 'open_raise' in self.preflop_table or 'metadata' in self.preflop_table
        
        if is_new_format:
            return self._get_recommendation_new_format(hand, position, num_players, has_raise, num_raises)
        else:
            return self._get_recommendation_old_format(hand, position, num_players, has_raise, num_raises)
    
    def _get_recommendation_new_format(self, hand: str, position: str, num_players: int,
                                      has_raise: bool, num_raises: int) -> str:
        """Obtiene recomendación usando el nuevo formato JSON con situaciones específicas"""
        
        # Determinar qué situación usar según el contexto
        # Si hay raises previos, usar tablas de 3Bet/4Bet
        # Si no hay raises, usar Open Raise
        
        if num_raises >= 2:
            # Situación: vs 4Bet (ya hubo 3Bet y 4Bet)
            return self._get_action_from_4bet_situation(hand, position)
        elif has_raise or num_raises >= 1:
            # Situación: vs 3Bet (alguien hizo raise/3Bet)
            return self._get_action_from_3bet_situation(hand, position)
        else:
            # Situación: Open Raise (nadie ha subido)
            return self._get_action_from_open_raise(hand, position)
    
    def _get_action_from_open_raise(self, hand: str, position: str) -> str:
        """Obtiene acción desde tablas de Open Raise"""
        if 'open_raise' not in self.preflop_table:
            return 'fold'
        
        # Usar IP (In Position) por defecto, ya que es más común
        # En el futuro se podría determinar si estamos IP o OOP
        if 'IP' in self.preflop_table['open_raise']:
            if 'OR_2.5bb_vs_3B_4x' in self.preflop_table['open_raise']['IP']:
                or_data = self.preflop_table['open_raise']['IP']['OR_2.5bb_vs_3B_4x']
                if position in or_data:
                    hands_dict = or_data[position]
                    # Verificar si la mano está en raise o fold
                    if 'raise' in hands_dict and hand in hands_dict['raise']:
                        return 'raise'
                    elif 'fold' in hands_dict and hand in hands_dict['fold']:
                        return 'fold'
        
        # Si no se encuentra, intentar OOP
        if 'OOP' in self.preflop_table['open_raise']:
            if 'OR_2.5bb_vs_3B_3x' in self.preflop_table['open_raise']['OOP']:
                or_data = self.preflop_table['open_raise']['OOP']['OR_2.5bb_vs_3B_3x']
                if position in or_data:
                    hands_dict = or_data[position]
                    if 'raise' in hands_dict and hand in hands_dict['raise']:
                        return 'raise'
                    elif 'fold' in hands_dict and hand in hands_dict['fold']:
                        return 'fold'
        
        return 'fold'
    
    def _get_action_from_3bet_situation(self, hand: str, position: str) -> str:
        """Obtiene acción desde tablas de 3Bet/Defend vs Open Raise"""
        if 'vs_open_raise' not in self.preflop_table:
            return 'fold'
        
        # Buscar en 3bet_defend
        if '3bet_defend' in self.preflop_table['vs_open_raise']:
            # Usar la situación más común: BT_CO_MP_3x_vs_OR_2.5bb_vs_4B_to_24bb
            situation_key = 'BT_CO_MP_3x_vs_OR_2.5bb_vs_4B_to_24bb'
            if situation_key in self.preflop_table['vs_open_raise']['3bet_defend']:
                situation_data = self.preflop_table['vs_open_raise']['3bet_defend'][situation_key]
                if position in situation_data:
                    hands_dict = situation_data[position]
                    # Verificar 3bet, fold, o call
                    if '3bet' in hands_dict and hand in hands_dict['3bet']:
                        return '3bet'
                    elif 'fold' in hands_dict and hand in hands_dict['fold']:
                        return 'fold'
                    elif 'call' in hands_dict and hand in hands_dict['call']:
                        return 'call'
        
        return 'fold'
    
    def _get_action_from_4bet_situation(self, hand: str, position: str) -> str:
        """Obtiene acción desde tablas de 4Bet"""
        if 'open_raise' not in self.preflop_table:
            return 'fold'
        
        # Buscar en 4B_to_24bb o 4B_to_25bb
        for position_type in ['IP', 'OOP']:
            if position_type in self.preflop_table['open_raise']:
                for situation_key in ['4B_to_24bb', '4B_to_25bb']:
                    if situation_key in self.preflop_table['open_raise'][position_type]:
                        fourbet_data = self.preflop_table['open_raise'][position_type][situation_key]
                        if position in fourbet_data:
                            hands_dict = fourbet_data[position]
                            # Verificar 4bet o fold
                            if '4bet' in hands_dict and hand in hands_dict['4bet']:
                                return '3bet'  # 4bet se mapea a 3bet en la UI
                            elif 'fold' in hands_dict and hand in hands_dict['fold']:
                                return 'fold'
        
        return 'fold'
    
    def _get_recommendation_old_format(self, hand: str, position: str, num_players: int,
                                       has_raise: bool, num_raises: int) -> str:
        """Obtiene recomendación usando el formato antiguo (compatibilidad)"""
        # Mapear posición del nuevo formato al antiguo si es necesario
        position_map = {
            'EP': 'early',
            'MP': 'middle',
            'CO': 'late',
            'BTN': 'late',
            'SB': 'late',
            'BB': 'late'
        }
        old_position = position_map.get(position, position)
        
        # Buscar en la tabla
        if hand not in self.preflop_table:
            return 'fold'
        
        # Obtener recomendación según número de jugadores
        position_data = self.preflop_table[hand].get(old_position, {})
        
        # Determinar rango de jugadores
        if num_players <= 3:
            players_key = '2-3'
        elif num_players <= 6:
            players_key = '4-6'
        else:
            players_key = '7-10'
        
        base_action = position_data.get(players_key, 'fold')
        
        # Ajustar según acciones previas
        if has_raise and base_action == 'raise':
            if num_raises >= 2:
                if hand in ['AA', 'KK']:
                    return 'all-in'
                else:
                    return '3bet'
            else:
                return '3bet'
        elif has_raise and base_action == 'call':
            if hand not in ['AA', 'KK', 'QQ', 'AKs', 'AKo', 'JJ', 'AQs']:
                return 'fold'
            else:
                return 'call'
        
        return base_action
    
    def get_action_description(self, action: str) -> str:
        """Convierte acción en descripción legible"""
        descriptions = {
            'fold': 'Retirarse (Fold)',
            'call': 'Igualar (Call)',
            'raise': 'Subir (Raise)',
            '3bet': 'Re-subir (3-Bet)',
            '4bet': 'Re-subir (4-Bet)',
            'all-in': 'Ir a por todo (All-in)',
            'defend': 'Defender (Call/3Bet)'
        }
        return descriptions.get(action, action)
    
    def save_table_to_file(self, filename: str = "preflop_strategy.json"):
        """Guarda la tabla actual en un archivo"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.preflop_table, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False


class PokerApp:
    """Aplicación principal con interfaz gráfica"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Probabilidades de Poker - Torneo")
        self.root.geometry("1600x1000")
        # Estilo más moderno
        self.root.configure(bg="#0a1a0a")
        
        self.my_cards = []
        self.community_cards = []
        self.num_players = 2
        self.active_players = 2  # Jugadores que no se han retirado
        
        # Variable para el combobox de jugadores
        self.players_var = tk.StringVar(value="2")
        self.players_combobox = None
        
        # Jugadores que se han retirado (fold)
        self.folded_players = set()
        
        # Acciones de cada jugador (para mostrar en la mesa)
        self.player_actions = {}  # {player_id: 'raise', 'call', 'fold', None}
        
        # Datos de probabilidad para mostrar en la mesa
        self.current_probability = None
        self.current_top_losing_hands = []
        
        # Flag para cancelar cálculos en curso
        self.calculation_in_progress = False
        self.calculation_thread = None
        
        # Timer para delay al recalcular cuando un jugador se retira
        self.fold_delay_timer = None
        
        # Posición del dealer (0 = dealer/button, 1 = SB, 2 = BB, etc.)
        self.dealer_position = 0
        # Tu posición en la mesa (índice del jugador, 0 = tú)
        self.my_position = 0
        
        # Acciones previas en la ronda (para determinar si hacer raise o 3bet)
        self.previous_actions = {
            'has_raise': False,  # Si alguien ya subió antes
            'has_call': False,   # Si alguien igualó antes
            'num_raises': 0      # Número de raises previos
        }
        
        # Ya no usamos estado de revelación, se detecta automáticamente por número de cartas
        
        # Diccionarios para rastrear botones de cartas seleccionadas
        self.my_card_buttons = {}  # {card: button}
        self.community_card_buttons = {}  # {card: button}
        
        # Referencias a los elementos gráficos de jugadores
        self.player_widgets = {}  # {player_id: widget}
        
        # Rangos y palos
        self.ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
        self.suits = {
            '♥': 'Corazones',
            '♠': 'Picas', 
            '♦': 'Diamantes',
            '♣': 'Tréboles'
        }
        
        self.calculator = ProbabilityCalculator()
        self.preflop_strategy = PreflopStrategy()
        
        # Recomendación preflop actual
        self.current_preflop_recommendation = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ========== MESA GRÁFICA (TODO EN UNO) ==========
        self.setup_table_view(main_frame)
    
    def setup_table_view(self, parent):
        """Configura la vista gráfica de la mesa"""
        # Canvas para dibujar la mesa (ocupa toda la ventana)
        # Fondo oscuro estilo casino
        self.table_canvas = tk.Canvas(parent, bg="#0a1a0a")
        self.table_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Redibujar cuando cambia el tamaño
        self.table_canvas.bind("<Configure>", lambda e: self.draw_table())
        
        # Dibujar la mesa inicial
        self.root.after(100, self.draw_table)
        
        # Variables para ventanas emergentes
        self.card_selector_window = None
    
    def setup_controls_panel(self, parent):
        """Configura el panel de controles y selección de cartas"""
        # Título
        title_label = ttk.Label(parent, text="Controles", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Canvas scrollable para los controles
        controls_canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=controls_canvas.yview)
        scrollable_frame = ttk.Frame(controls_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: controls_canvas.configure(scrollregion=controls_canvas.bbox("all"))
        )
        
        controls_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        controls_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scroll con rueda del ratón
        def on_mousewheel(event):
            try:
                if event.delta:
                    controls_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif event.num == 4:
                    controls_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    controls_canvas.yview_scroll(1, "units")
            except:
                pass
        
        def bind_to_mousewheel(event):
            controls_canvas.bind_all("<MouseWheel>", on_mousewheel)
            controls_canvas.bind_all("<Button-4>", on_mousewheel)
            controls_canvas.bind_all("<Button-5>", on_mousewheel)
        
        def unbind_from_mousewheel(event):
            controls_canvas.unbind_all("<MouseWheel>")
            controls_canvas.unbind_all("<Button-4>")
            controls_canvas.unbind_all("<Button-5>")
        
        controls_canvas.bind("<Enter>", bind_to_mousewheel)
        controls_canvas.bind("<Leave>", unbind_from_mousewheel)
        scrollable_frame.bind("<Enter>", bind_to_mousewheel)
        scrollable_frame.bind("<Leave>", unbind_from_mousewheel)
        
        controls_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = scrollable_frame
        
        # Mis cartas - Selector visual
        my_cards_label = ttk.Label(main_frame, text="Mis Cartas (selecciona 2)", 
                                   font=("Arial", 14, "bold"))
        my_cards_label.pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        self.my_cards_selected_label = ttk.Label(main_frame, text="Seleccionadas: 0/2", 
                                                  font=("Arial", 10), foreground="blue")
        self.my_cards_selected_label.pack(pady=5, padx=10, anchor=tk.W)
        
        my_cards_container = ttk.LabelFrame(main_frame, text="Selecciona tus 2 cartas", padding="10")
        my_cards_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Crear selectores por palo para mis cartas
        self.create_card_selector(my_cards_container, "my", self.ranks, self.suits)
        
        # Cartas comunitarias - Selector visual (inicialmente deshabilitado)
        community_label = ttk.Label(main_frame, text="Cartas Comunitarias", 
                                   font=("Arial", 14, "bold"))
        community_label.pack(pady=(20, 5), padx=10, anchor=tk.W)
        
        # Botones para revelar cartas progresivamente
        reveal_frame = ttk.Frame(main_frame)
        reveal_frame.pack(pady=5, padx=10)
        
        ttk.Label(reveal_frame, text="Revelar cartas:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        self.reveal_flop_btn = ttk.Button(reveal_frame, text="Flop (3 cartas)", 
                                          command=self.reveal_flop, state=tk.DISABLED)
        self.reveal_flop_btn.pack(side=tk.LEFT, padx=3)
        
        self.reveal_turn_btn = ttk.Button(reveal_frame, text="Turn (1 carta)", 
                                          command=self.reveal_turn, state=tk.DISABLED)
        self.reveal_turn_btn.pack(side=tk.LEFT, padx=3)
        
        self.reveal_river_btn = ttk.Button(reveal_frame, text="River (1 carta)", 
                                          command=self.reveal_river, state=tk.DISABLED)
        self.reveal_river_btn.pack(side=tk.LEFT, padx=3)
        
        ttk.Button(reveal_frame, text="Ocultar todas", 
                  command=self.hide_all_community).pack(side=tk.LEFT, padx=10)
        
        self.community_selected_label = ttk.Label(main_frame, text="Reveladas: 0/5", 
                                                   font=("Arial", 10), foreground="gray")
        self.community_selected_label.pack(pady=5, padx=10, anchor=tk.W)
        
        community_container = ttk.LabelFrame(main_frame, text="Cartas comunitarias (selecciona cuando se revelen)", padding="10")
        community_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Crear selectores por palo para cartas comunitarias (inicialmente deshabilitados)
        self.create_card_selector(community_container, "community", self.ranks, self.suits)
        
        # Deshabilitar todos los botones de cartas comunitarias inicialmente
        self.update_community_buttons_state()
        
        # Botones de acción
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20, padx=10)
        
        ttk.Button(buttons_frame, text="Calcular Probabilidad", 
                  command=self.calculate_and_display, 
                  width=25).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Limpiar Todo", 
                  command=self.clear_all, width=20).pack(side=tk.LEFT, padx=5)
        
        # Resultado
        result_frame = ttk.LabelFrame(main_frame, text="Resultado", padding="15")
        result_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.probability_label = ttk.Label(result_frame, text="Probabilidad: --", 
                                          font=("Arial", 16, "bold"))
        self.probability_label.pack(pady=5)
        
        self.hand_type_label = ttk.Label(result_frame, text="", font=("Arial", 11))
        self.hand_type_label.pack(pady=5)
        
        self.top_losing_hands_label = ttk.Label(result_frame, text="", font=("Arial", 10), 
                                                foreground="red", justify=tk.LEFT)
        self.top_losing_hands_label.pack(pady=(10, 0), anchor=tk.W)
    
    def draw_table(self):
        """Dibuja la mesa de poker y los jugadores"""
        self.table_canvas.delete("all")
        
        width = self.table_canvas.winfo_width()
        height = self.table_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            # Si el canvas aún no tiene tamaño, programar redibujado
            self.root.after(100, self.draw_table)
            return
        
        center_x = width // 2
        center_y = height // 2
        
        # Dibujar mesa (óvalo) con diseño más profesional
        table_width = min(width * 0.75, 600)
        table_height = min(height * 0.65, 400)
        
        # Sombra de la mesa
        shadow_offset = 8
        self.table_canvas.create_oval(
            center_x - table_width // 2 + shadow_offset, 
            center_y - table_height // 2 + shadow_offset,
            center_x + table_width // 2 + shadow_offset, 
            center_y + table_height // 2 + shadow_offset,
            fill="#000000", outline="", width=0
        )
        
        # Mesa principal con color verde fieltro
        self.table_canvas.create_oval(
            center_x - table_width // 2, center_y - table_height // 2,
            center_x + table_width // 2, center_y + table_height // 2,
            fill="#0d4a1f", outline="#1a6b2e", width=4
        )
        
        # Borde interior de la mesa
        inner_margin = 15
        self.table_canvas.create_oval(
            center_x - table_width // 2 + inner_margin, 
            center_y - table_height // 2 + inner_margin,
            center_x + table_width // 2 - inner_margin, 
            center_y + table_height // 2 - inner_margin,
            fill="", outline="#2d8f4f", width=2
        )
        
        # Dibujar controles en el canvas
        self.draw_controls()
        
        # Dibujar información de probabilidad en la esquina superior izquierda
        self.draw_probability_info()
        
        # Dibujar jugadores alrededor de la mesa
        self.draw_players(center_x, center_y, table_width, table_height)
        
        # Dibujar cartas comunitarias en el centro
        self.draw_community_cards(center_x, center_y)
    
    def draw_players(self, center_x, center_y, table_width, table_height):
        """Dibuja los jugadores alrededor de la mesa"""
        num_players = self.num_players
        
        # Validar número de jugadores
        if num_players < 2:
            num_players = 2
            self.num_players = 2
        elif num_players > 10:
            num_players = 10
            self.num_players = 10
        
        radius_x = table_width // 2 + 80
        radius_y = table_height // 2 + 80
        
        # Limpiar widgets de jugadores anteriores
        try:
            for player_id, widgets in list(self.player_widgets.items()):
                for widget in widgets:
                    try:
                        if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                            widget.destroy()
                    except:
                        pass
        except:
            pass
        self.player_widgets.clear()
        
        # Limpiar también las ventanas del canvas
        self.table_canvas.delete("player_*_actions")
        
        # Distribución uniforme de TODOS los jugadores alrededor de toda la mesa (360 grados)
        # El jugador 0 (tú) siempre está arriba (90 grados)
        # Todos los jugadores se distribuyen uniformemente, pero rotamos la distribución
        # para que el jugador 0 siempre esté en 90°
        fixed_positions = []
        
        # Calcular espaciado uniforme para TODOS los jugadores
        # Espaciado = 360 / num_players (distribución uniforme alrededor del círculo)
        spacing_deg = 360.0 / num_players
        
        # Generar posiciones para TODOS los jugadores
        # Empezamos desde 90° (donde queremos que esté el jugador 0) y distribuimos uniformemente
        for slot in range(num_players):
            # Calcular el ángulo: empezamos desde 90° y avanzamos con el espaciado uniforme
            # El jugador 0 (slot 0) estará en 90°, el jugador 1 en 90° + spacing, etc.
            angle_deg = (90 + slot * spacing_deg) % 360
            
            # Convertir a coordenadas
            angle = math.radians(angle_deg)
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            
            fixed_positions.append((slot, x, y, angle_deg))
        
        # Ahora dibujar solo los jugadores que están activos (0 a num_players-1)
        for i in range(num_players):
            if i < len(fixed_positions):
                # fixed_positions puede tener 3 o 4 elementos (con o sin ángulo)
                try:
                    if len(fixed_positions[i]) == 4:
                        slot_id, x, y, angle_deg = fixed_positions[i]
                    else:
                        slot_id, x, y = fixed_positions[i]
                        angle_deg = None
                except (ValueError, IndexError, TypeError):
                    # Si hay error, saltar este jugador
                    continue
            else:
                continue  # Si no hay posición fija, saltar este jugador
            # Determinar si el jugador está retirado
            is_folded = i in self.folded_players
            is_dealer = i == self.dealer_position
            player_action = self.player_actions.get(i, None)
            
            # Dibujar fondo del jugador (círculo con sombra)
            player_radius = 40
            shadow_offset = 3
            
            # Sombra
            self.table_canvas.create_oval(
                x - player_radius + shadow_offset, y - player_radius + shadow_offset,
                x + player_radius + shadow_offset, y + player_radius + shadow_offset,
                fill="#000000", outline="", width=0, tags=f"player_{i}"
            )
            
            # Círculo principal
            if is_folded:
                player_color = "#3a3a3a"
                outline_color = "#666666"
                text_color = "#999999"
            elif is_dealer:
                player_color = "#f59e0b"  # Naranja para dealer
                outline_color = "#fbbf24"
                text_color = "#ffffff"
            else:
                player_color = "#1e3a8a" if i == 0 else "#4a5568"
                outline_color = "#60a5fa" if i == 0 else "#9ca3af"
                text_color = "#ffffff"
            
            self.table_canvas.create_oval(
                x - player_radius, y - player_radius,
                x + player_radius, y + player_radius,
                fill=player_color, outline=outline_color, width=3,
                tags=f"player_{i}"
            )
            
            # Borde interior
            self.table_canvas.create_oval(
                x - player_radius + 3, y - player_radius + 3,
                x + player_radius - 3, y + player_radius - 3,
                fill="", outline="#ffffff", width=1,
                tags=f"player_{i}"
            )
            
            # Indicador de dealer (D)
            if is_dealer:
                self.table_canvas.create_text(
                    x - player_radius + 8, y - player_radius + 8,
                    text="D", fill="#fbbf24", font=("Arial", 10, "bold"),
                    anchor=tk.NW, tags=f"player_{i}"
                )
            
            # Texto del jugador
            player_text = "TÚ" if i == 0 else f"J{i}"
            if is_folded:
                player_text += "\n✗"
            
            self.table_canvas.create_text(
                x, y - 5, text=player_text, fill=text_color,
                font=("Arial", 11, "bold"), tags=f"player_{i}"
            )
            
            # Botones de acción debajo de cada jugador (excepto el jugador 0)
            if i != 0 and not is_folded:
                # Crear frame para los botones de acción
                action_frame = tk.Frame(self.table_canvas, bg="#0a1a0a")
                
                # Posición de los botones (debajo del jugador)
                button_y = y + player_radius + 10
                
                # Botones de acción
                actions = [
                    ('raise', '↑', '#10b981'),
                    ('call', '=', '#f59e0b'),
                    ('fold', '✗', '#ef4444'),
                    ('3bet', '3', '#8b5cf6'),
                    ('all-in', 'A', '#dc2626')
                ]
                
                # Determinar qué botón está activo
                current_action = self.player_actions.get(i, None)
                
                for action, symbol, color in actions:
                    # Crear botón
                    btn = tk.Button(
                        action_frame,
                        text=symbol,
                        width=2,
                        height=1,
                        bg=color if current_action == action else '#4a5568',
                        fg='white',
                        font=("Arial", 8, "bold"),
                        relief=tk.RAISED if current_action == action else tk.FLAT,
                        bd=2 if current_action == action else 1,
                        command=lambda p=i, a=action: self.set_player_action(p, a if self.player_actions.get(p) != a else None)
                    )
                    btn.pack(side=tk.LEFT, padx=1)
                
                # Posicionar el frame de botones debajo del jugador
                self.table_canvas.create_window(
                    x, button_y,
                    window=action_frame,
                    anchor=tk.CENTER,
                    tags=f"player_{i}_actions"
                )
                
                # Guardar referencia al frame
                if i not in self.player_widgets:
                    self.player_widgets[i] = []
                self.player_widgets[i].append(action_frame)
            
            # Chips del jugador (pequeños círculos decorativos)
            if not is_folded:
                chip_y = y + player_radius - 8
                chip_colors = ["#dc2626", "#fbbf24", "#3b82f6"]
                for chip_idx in range(3):
                    chip_x = x - 12 + chip_idx * 12
                    self.table_canvas.create_oval(
                        chip_x - 4, chip_y - 4,
                        chip_x + 4, chip_y + 4,
                        fill=chip_colors[chip_idx % len(chip_colors)],
                        outline="#ffffff", width=1,
                        tags=f"player_{i}"
                    )
            
            # Hacer clicable para cambiar dealer (click izquierdo)
            # Los botones de acción ya están debajo de cada jugador
            if i <= 10:  # No puedes cambiar tu propia posición
                self.table_canvas.tag_bind(f"player_{i}", "<Button-1>", 
                                          lambda e, p=i: self.set_dealer(p))
            
            # Si es el jugador 0 (tú), mostrar cuadrados para cartas y probabilidad
            if i == 0:
                # Dibujar cuadrados para las cartas (encima del círculo)
                self.draw_my_card_slots(x, y - 60)
                
                # Mostrar probabilidad debajo del círculo con fondo
                if self.current_probability is not None:
                    prob_text = f"{self.current_probability * 100:.1f}%"
                    if self.current_probability > 0.5:
                        prob_color = "#10b981"
                        bg_color = "#064e3b"
                    elif self.current_probability > 0.25:
                        prob_color = "#f59e0b"
                        bg_color = "#78350f"
                    else:
                        prob_color = "#ef4444"
                        bg_color = "#7f1d1d"
                    
                    prob_y = y + player_radius + 25
                    # Fondo de la probabilidad
                    self.table_canvas.create_rectangle(
                        x - 35, prob_y - 10,
                        x + 35, prob_y + 10,
                        fill=bg_color, outline=prob_color, width=2,
                        tags=f"player_{i}_prob"
                    )
                    
                    self.table_canvas.create_text(
                        x, prob_y, text=prob_text, fill=prob_color,
                        font=("Arial", 13, "bold"), tags=f"player_{i}_prob"
                    )
                
                # Mostrar recomendación preflop si no hay cartas comunitarias
                if len(self.community_cards) == 0 and len(self.my_cards) == 2:
                    self.draw_preflop_recommendation(x, y, player_radius)
    
    def draw_card(self, canvas, x, y, card, card_width, card_height, tags=""):
        """Dibuja una carta con diseño realista"""
        # Coordenadas
        rect_x1 = x - card_width // 2
        rect_y1 = y - card_height // 2
        rect_x2 = x + card_width // 2
        rect_y2 = y + card_height // 2
        
        # Sombra de la carta
        shadow_offset = 3
        canvas.create_rectangle(
            rect_x1 + shadow_offset, rect_y1 + shadow_offset,
            rect_x2 + shadow_offset, rect_y2 + shadow_offset,
            fill="#000000", outline="", width=0, tags=tags
        )
        
        # Carta principal (blanca)
        canvas.create_rectangle(
            rect_x1, rect_y1, rect_x2, rect_y2,
            fill="#ffffff", outline="#333333", width=2,
            tags=tags
        )
        
        # Borde interior
        border_margin = 3
        canvas.create_rectangle(
            rect_x1 + border_margin, rect_y1 + border_margin,
            rect_x2 - border_margin, rect_y2 - border_margin,
            fill="", outline="#e0e0e0", width=1,
            tags=tags
        )
        
        if card:
            # Determinar color
            text_color = "#dc143c" if card[1] in ['♥', '♦'] else "#000000"
            suit = card[1]
            rank = card[0] if card[0] != 'T' else '10'
            
            # Rango superior izquierdo
            canvas.create_text(
                x - card_width // 2 + 8, y - card_height // 2 + 10,
                text=rank, fill=text_color, font=("Arial", 12, "bold"),
                anchor=tk.NW, tags=tags
            )
            canvas.create_text(
                x - card_width // 2 + 8, y - card_height // 2 + 22,
                text=suit, fill=text_color, font=("Arial", 10),
                anchor=tk.NW, tags=tags
            )
            
            # Palo grande en el centro
            canvas.create_text(
                x, y, text=suit, fill=text_color,
                font=("Arial", 20, "bold"), tags=tags
            )
            
            # Rango inferior derecho (invertido)
            canvas.create_text(
                x + card_width // 2 - 8, y + card_height // 2 - 10,
                text=rank, fill=text_color, font=("Arial", 12, "bold"),
                anchor=tk.SE, tags=tags
            )
            canvas.create_text(
                x + card_width // 2 - 8, y + card_height // 2 - 22,
                text=suit, fill=text_color, font=("Arial", 10),
                anchor=tk.SE, tags=tags
            )
    
    def draw_my_card_slots(self, x, y):
        """Dibuja los cuadrados clicables para las cartas del jugador"""
        card_width = 50
        card_height = 70
        spacing = 12
        
        # Crear lista de 2 posiciones para mostrar (mantener orden)
        display_cards = [None, None]
        if len(self.my_cards) >= 1:
            display_cards[0] = self.my_cards[0]
        if len(self.my_cards) >= 2:
            display_cards[1] = self.my_cards[1]
        
        for idx in range(2):
            card_x = x - (card_width + spacing) / 2 + idx * (card_width + spacing)
            
            # Calcular coordenadas del rectángulo
            rect_x1 = card_x - card_width // 2
            rect_y1 = y - card_height // 2
            rect_x2 = card_x + card_width // 2
            rect_y2 = y + card_height // 2
            
            # Si hay carta en esta posición, mostrarla
            if display_cards[idx] is not None:
                card = display_cards[idx]
                self.draw_card(self.table_canvas, card_x, y, card, card_width, card_height, f"my_card_{idx}")
            else:
                # Dibujar carta boca abajo (diseño de carta oculta)
                # Sombra
                shadow_offset = 3
                self.table_canvas.create_rectangle(
                    rect_x1 + shadow_offset, rect_y1 + shadow_offset,
                    rect_x2 + shadow_offset, rect_y2 + shadow_offset,
                    fill="#000000", outline="", width=0, tags=f"my_card_{idx}"
                )
                
                # Carta boca abajo (azul oscuro con patrón)
                self.table_canvas.create_rectangle(
                    rect_x1, rect_y1, rect_x2, rect_y2,
                    fill="#1a237e", outline="#3f51b5", width=2,
                    tags=f"my_card_{idx}"
                )
                
                # Patrón decorativo
                pattern_color = "#283593"
                for i in range(3):
                    for j in range(4):
                        self.table_canvas.create_oval(
                            rect_x1 + 8 + i * 12, rect_y1 + 8 + j * 15,
                            rect_x1 + 12 + i * 12, rect_y1 + 12 + j * 15,
                            fill=pattern_color, outline="", width=0,
                            tags=f"my_card_{idx}"
                        )
            
            # Crear un rectángulo invisible más grande para hacer toda el área clicable
            # Esto asegura que se pueda hacer clic en cualquier parte del cuadrado
            self.table_canvas.create_rectangle(
                rect_x1 - 2, rect_y1 - 2, rect_x2 + 2, rect_y2 + 2,
                fill="", outline="", width=0,
                tags=f"my_card_{idx}_clickable"
            )
            
            # Hacer TODO clicable (tanto el rectángulo visible como el invisible)
            self.table_canvas.tag_bind(f"my_card_{idx}", "<Button-1>", 
                                     lambda e, idx=idx: self.open_card_selector("my", idx))
            self.table_canvas.tag_bind(f"my_card_{idx}", "<Button-3>", 
                                     lambda e, idx=idx: self.remove_my_card(idx))
            self.table_canvas.tag_bind(f"my_card_{idx}_clickable", "<Button-1>", 
                                     lambda e, idx=idx: self.open_card_selector("my", idx))
            self.table_canvas.tag_bind(f"my_card_{idx}_clickable", "<Button-3>", 
                                     lambda e, idx=idx: self.remove_my_card(idx))
    
    def draw_preflop_recommendation(self, x, y, player_radius):
        """Dibuja la recomendación de apuesta preflop según el número de jugadores actuales"""
        if len(self.my_cards) != 2:
            return
        
        # Obtener recomendación según posición y número de jugadores actuales
        position = self.preflop_strategy.get_position(
            self.my_position, self.num_players, self.dealer_position
        )
        recommendation = self.preflop_strategy.get_recommendation(
            self.my_cards[0], self.my_cards[1], position, self.num_players,
            self.previous_actions['has_raise'], self.previous_actions['num_raises']
        )
        
        # Colores según acción
        action_colors = {
            'fold': ('#ef4444', '#7f1d1d'),  # Rojo
            'call': ('#f59e0b', '#78350f'),   # Naranja
            'raise': ('#10b981', '#064e3b'),  # Verde
            '3bet': ('#3b82f6', '#1e3a8a'),   # Azul
            '4bet': ('#8b5cf6', '#5b21b6'),   # Púrpura
            'all-in': ('#dc2626', '#991b1b'),  # Rojo oscuro
            'defend': ('#06b6d4', '#0891b2')   # Cyan
        }
        
        text_color, bg_color = action_colors.get(recommendation, ('#ffffff', '#1a1a1a'))
        action_text = self.preflop_strategy.get_action_description(recommendation)
        
        # Dibujar recomendación encima de las cartas
        rec_y = y - player_radius - 90
        
        # Sombra
        shadow_offset = 2
        self.table_canvas.create_rectangle(
            x - 65 + shadow_offset, rec_y - 12 + shadow_offset,
            x + 65 + shadow_offset, rec_y + 12 + shadow_offset,
            fill="#000000", outline="", width=0,
            tags="preflop_rec"
        )
        
        # Fondo
        self.table_canvas.create_rectangle(
            x - 65, rec_y - 12,
            x + 65, rec_y + 12,
            fill=bg_color, outline=text_color, width=2,
            tags="preflop_rec"
        )
        
        # Texto con número de jugadores
        players_text = f"{self.active_players} jugadores"
        self.table_canvas.create_text(
            x, rec_y - 5, text=players_text, fill="#cccccc",
            font=("Arial", 8), tags="preflop_rec"
        )
        
        # Texto de la acción
        self.table_canvas.create_text(
            x, rec_y + 5, text=action_text, fill=text_color,
            font=("Arial", 11, "bold"), tags="preflop_rec"
        )
    
    def draw_controls(self):
        """Dibuja los controles en el canvas"""
        width = self.table_canvas.winfo_width()
        height = self.table_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Fondo de controles - más ancho para los nuevos controles
        control_bg_y = 10
        control_bg_height = 75
        control_bg_width = 650
        self.table_canvas.create_rectangle(
            10, control_bg_y, 10 + control_bg_width, control_bg_y + control_bg_height,
            fill="#1a1a1a", outline="#444444", width=2
        )
        
        # Borde interior
        self.table_canvas.create_rectangle(
            12, control_bg_y + 2, 8 + control_bg_width, control_bg_y + control_bg_height - 2,
            fill="", outline="#666666", width=1
        )
        
        # Controles en la parte superior - Fila 1
        control_y = 25
        
        # Número de jugadores - Etiqueta
        label_x = 20
        self.table_canvas.create_text(label_x, control_y, text="Jugadores:", 
                                      fill="#93c5fd", font=("Arial", 11, "bold"), anchor=tk.NW)
        
        # Crear combobox (desplegable) como widget flotante (usando create_window)
        # Sincronizar el valor actual
        self.players_var.set(str(self.num_players))
        
        # Eliminar widget anterior si existe
        if hasattr(self, 'players_combobox_window_id'):
            try:
                self.table_canvas.delete(self.players_combobox_window_id)
            except:
                pass
        
        # Crear frame para el combobox
        combobox_frame = ttk.Frame(self.table_canvas)
        self.players_combobox = ttk.Combobox(combobox_frame, 
                                             textvariable=self.players_var,
                                             values=[str(i) for i in range(2, 11)],  # 2 a 10
                                             width=6,
                                             state="readonly",  # No se puede escribir
                                             font=("Arial", 10))
        self.players_combobox.pack()
        
        # Configurar callback cuando cambie el valor - siempre reconfigurar el bind
        self.players_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_table_players())
        
        # Posicionar combobox después del texto "Jugadores:" (aprox 100px desde el inicio)
        combobox_x = 120
        self.players_combobox_window_id = self.table_canvas.create_window(combobox_x, control_y - 2, window=combobox_frame, anchor=tk.NW)
        
        # Jugadores activos con fondo - después del spinbox
        active_text = f"Activos: {self.active_players}"
        active_bg_x = 220  # Más espacio después del spinbox
        active_bg_width = 110
        self.table_canvas.create_rectangle(
            active_bg_x, control_y - 5, active_bg_x + active_bg_width, control_y + 20,
            fill="#064e3b", outline="#10b981", width=1
        )
        self.table_canvas.create_text(active_bg_x + 5, control_y, text=active_text, 
                                      fill="#34d399", font=("Arial", 11, "bold"), anchor=tk.NW)
        
        # Información sobre controles
        info_bg_x = 340
        info_text = "Clic izq en jugador = Dealer | Clic der = Acción (↑/=/✗)"
        self.table_canvas.create_text(info_bg_x, control_y, text=info_text, 
                                      fill="#cccccc", font=("Arial", 8), anchor=tk.NW)
        
        # Botón para limpiar todo - Fila 2 (debajo)
        button_y = control_y + 40
        if hasattr(self, 'clear_btn_window_id'):
            try:
                self.table_canvas.delete(self.clear_btn_window_id)
            except:
                pass
        
        clear_frame = ttk.Frame(self.table_canvas)
        clear_btn = tk.Button(clear_frame, text="🔄 Limpiar Todo", 
                             command=self.clear_all,
                             bg="#7f1d1d", fg="#fca5a5", 
                             font=("Arial", 10, "bold"),
                             relief=tk.RAISED, bd=2,
                             activebackground="#991b1b", activeforeground="#ffffff",
                             padx=10, pady=5)
        clear_btn.pack()
        self.clear_btn_window_id = self.table_canvas.create_window(20, button_y, window=clear_frame, anchor=tk.NW)
        
        # Instrucciones con fondo
        inst_y = height - 25
        self.table_canvas.create_rectangle(
            10, inst_y - 20, width - 10, height - 5,
            fill="#1a1a1a", outline="#444444", width=1
        )
        self.table_canvas.create_text(15, inst_y, 
                                      text="Clic izq en jugador = Dealer | Clic der = Acción (↑ Raise / = Call / ✗ Fold) | Clic en cartas = Seleccionar",
                                      fill="#cccccc", font=("Arial", 9), anchor=tk.SW)
    
    def handle_reveal_button(self):
        """Maneja el clic en el botón de revelar"""
        if not self.community_revealed['flop']:
            self.reveal_flop()
        elif not self.community_revealed['turn']:
            self.reveal_turn()
        elif not self.community_revealed['river']:
            self.reveal_river()
        else:
            self.hide_all_community()
    
    def open_card_selector(self, card_type, card_index):
        """Abre una ventana emergente para seleccionar una carta"""
        # Cerrar ventana anterior si existe
        if self.card_selector_window and self.card_selector_window.winfo_exists():
            self.card_selector_window.destroy()
        
        self.selecting_card_type = card_type
        self.selecting_card_index = card_index
        
        # Crear ventana emergente - más grande para que quepan todas las cartas
        selector_window = tk.Toplevel(self.root)
        selector_window.title("Seleccionar Carta")
        # Ventana más ancha para que quepan las 13 cartas por fila
        selector_window.geometry("900x550")
        selector_window.transient(self.root)
        selector_window.grab_set()
        
        self.card_selector_window = selector_window
        
        # Frame principal
        main_frame = ttk.Frame(selector_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Selecciona una carta:", 
                 font=("Arial", 14, "bold")).pack(pady=(5, 10))
        
        # Frame para las cartas sin scroll - todo visible
        selector_frame = ttk.Frame(main_frame)
        selector_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_card_selector_popup(selector_frame)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Botón eliminar (solo si hay carta en esta posición)
        has_card = False
        if card_type == "my" and card_index < len(self.my_cards):
            has_card = True
        elif card_type == "community" and card_index < len(self.community_cards):
            has_card = True
        
        if has_card:
            ttk.Button(button_frame, text="Eliminar Carta", 
                      command=lambda: self.remove_card_from_popup()).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancelar", 
                  command=selector_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_card_selector_popup(self, parent):
        """Crea el selector de cartas en la ventana emergente"""
        # Configurar columnas del parent para distribución uniforme
        parent.columnconfigure(0, weight=1)
        
        # Crear un frame para cada palo
        row = 0
        for suit_symbol, suit_name in self.suits.items():
            # Frame para este palo con menos padding para que quepan más cartas
            suit_frame = ttk.LabelFrame(parent, text=suit_name, padding="8")
            suit_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=10)
            
            # Configurar todas las columnas del suit_frame para distribución uniforme
            for i in range(len(self.ranks)):
                suit_frame.columnconfigure(i, weight=1, uniform="card_col")
            
            # Crear botones para cada rango - más pequeños para que quepan todos
            col = 0
            for rank in self.ranks:
                # Crear el texto de la carta
                card_text = f"{rank}{suit_symbol}"
                normalized_rank = rank if rank != '10' else '10'
                card_key = normalized_rank + suit_symbol
                normalized_card = self.normalize_card_format(card_key)
                
                # Verificar si la carta ya está en uso
                all_used_cards = self.my_cards + self.community_cards
                is_used = normalized_card in all_used_cards
                
                # Determinar el color del texto y fondo
                text_color = "#dc143c" if suit_symbol in ['♥', '♦'] else "#000000"
                bg_color = "#e0e0e0" if is_used else "#ffffff"
                active_bg = "#c0c0c0" if is_used else "#d0d0d0"
                
                # Crear botón más compacto para que quepan las 13 cartas
                btn = tk.Button(suit_frame, text=card_text, width=4, height=1,
                               font=("Arial", 10, "bold"), fg=text_color, bg=bg_color,
                               state=tk.DISABLED if is_used else tk.NORMAL,
                               activebackground=active_bg, activeforeground=text_color,
                               relief=tk.RAISED, bd=2,
                               command=lambda c=normalized_card: self.select_card_from_popup(c))
                
                btn.grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
                col += 1
            
            row += 1
    
    def remove_my_card(self, idx):
        """Elimina una carta propia"""
        # Crear lista de 2 posiciones
        cards_list = [None, None]
        if len(self.my_cards) > 0:
            cards_list[0] = self.my_cards[0]
        if len(self.my_cards) > 1:
            cards_list[1] = self.my_cards[1]
        
        # Eliminar la carta en la posición idx
        if idx < 2:
            cards_list[idx] = None
        
        # Actualizar lista
        self.my_cards = [c for c in cards_list if c is not None]
        
        self.draw_table()
        # Recalcular si tenemos 2 cartas
        if len(self.my_cards) == 2:
            self.update_probability()
        else:
            # Limpiar probabilidad si no hay suficientes cartas
            self.current_probability = None
            self.current_top_losing_hands = []
            self.draw_table()
    
    def remove_community_card(self, idx):
        """Elimina una carta comunitaria"""
        if idx < len(self.community_cards):
            self.community_cards.pop(idx)
            self.draw_table()
            # Recalcular si tenemos 2 cartas y 3+ comunitarias
            if len(self.my_cards) == 2 and len(self.community_cards) >= 3:
                self.update_probability()
            else:
                # Limpiar probabilidad si no hay suficientes cartas
                self.current_probability = None
                self.current_top_losing_hands = []
                self.draw_table()
    
    def remove_card_from_popup(self):
        """Elimina la carta desde el popup"""
        if self.selecting_card_type == "my":
            self.remove_my_card(self.selecting_card_index)
        else:
            self.remove_community_card(self.selecting_card_index)
        
        if self.card_selector_window:
            self.card_selector_window.destroy()
            self.card_selector_window = None
    
    def select_card_from_popup(self, card):
        """Selecciona una carta desde la ventana emergente"""
        if self.selecting_card_type == "my":
            # Verificar que la carta no esté ya en uso en comunitarias
            if card in self.community_cards:
                messagebox.showwarning("Carta en uso", 
                                     "Esta carta ya está seleccionada como comunitaria.\nDeselecciónala primero.")
                return
            
            # Crear lista de 2 posiciones para mantener el orden
            cards_list = [None, None]
            
            # Llenar las posiciones existentes (mantener orden)
            if len(self.my_cards) >= 1:
                cards_list[0] = self.my_cards[0]
            if len(self.my_cards) >= 2:
                cards_list[1] = self.my_cards[1]
            
            # Si la carta ya está en otra posición, quitarla
            for i in range(2):
                if cards_list[i] == card:
                    cards_list[i] = None
                    break
            
            # Colocar la carta en la posición seleccionada (0 o 1)
            if 0 <= self.selecting_card_index < 2:
                cards_list[self.selecting_card_index] = card
            
            # Actualizar la lista de cartas (solo las que no son None, manteniendo orden)
            self.my_cards = []
            for c in cards_list:
                if c is not None:
                    self.my_cards.append(c)
        
        else:  # community
            # Asegurar que tenemos espacio (máximo 5 cartas)
            if self.selecting_card_index >= 5:
                messagebox.showwarning("Error", "Solo puedes tener 5 cartas comunitarias")
                return
            
            # Asegurar que tenemos espacio en la lista
            while len(self.community_cards) <= self.selecting_card_index:
                self.community_cards.append(None)
            
            # Si ya hay una carta en esta posición, quitarla
            if self.community_cards[self.selecting_card_index] is not None:
                old_card = self.community_cards[self.selecting_card_index]
                if old_card in self.community_cards:
                    self.community_cards.remove(old_card)
            
            # Añadir la nueva carta
            if card not in self.community_cards:
                self.community_cards.insert(self.selecting_card_index, card)
            else:
                self.community_cards.remove(card)
                self.community_cards.insert(self.selecting_card_index, card)
            
            # Limpiar None y mantener orden
            self.community_cards = [c for c in self.community_cards if c is not None]
            
            # Limitar a 5 cartas
            if len(self.community_cards) > 5:
                self.community_cards = self.community_cards[:5]
        
        # Cerrar ventana y redibujar
        if self.card_selector_window:
            self.card_selector_window.destroy()
            self.card_selector_window = None
        
        self.draw_table()
        
        # Actualizar probabilidad automáticamente:
        # - Cuando hay 2 cartas propias (incluso sin comunitarias)
        # - O cuando hay 2 cartas propias y 3, 4 o 5 comunitarias
        if len(self.my_cards) == 2:
            self.update_probability()
    
    def draw_probability_info(self):
        """Dibuja la información de manos más probables en la esquina superior derecha"""
        if not self.current_top_losing_hands:
            return
        
        width = self.table_canvas.winfo_width()
        if width <= 1:
            return
        
        # Mover a la esquina superior derecha para evitar superposición
        info_x = width - 320
        info_y = 15
        
        # Fondo con borde y sombra
        bg_width = 300
        bg_height = 100 + len(self.current_top_losing_hands) * 22
        
        # Sombra
        self.table_canvas.create_rectangle(
            info_x - 3, info_y - 3,
            info_x + bg_width + 3, info_y + bg_height + 3,
            fill="#000000", outline="", width=0
        )
        
        # Fondo principal
        self.table_canvas.create_rectangle(
            info_x - 5, info_y - 5,
            info_x + bg_width, info_y + bg_height,
            fill="#1a1a1a", outline="#444444", width=2
        )
        
        # Borde interior
        self.table_canvas.create_rectangle(
            info_x - 3, info_y - 3,
            info_x + bg_width - 2, info_y + bg_height - 2,
            fill="", outline="#666666", width=1
        )
        
        # Título con fondo
        title_bg_y = info_y + 5
        self.table_canvas.create_rectangle(
            info_x, title_bg_y - 2,
            info_x + bg_width - 10, title_bg_y + 18,
            fill="#2d1b1b", outline="#dc2626", width=1
        )
        self.table_canvas.create_text(
            info_x + 5, title_bg_y + 8, text="⚠ Manos que te ganan:",
            fill="#ff6b6b", font=("Arial", 11, "bold"), anchor=tk.W
        )
        
        # Lista de manos
        y_offset = 35
        for i, (hand_name, count) in enumerate(self.current_top_losing_hands[:3]):
            percentage = (count / 20000) * 100
            hand_text = f"{i+1}. {hand_name}: {percentage:.1f}%"
            
            # Fondo para cada mano
            hand_bg_y = info_y + y_offset + i * 22
            self.table_canvas.create_rectangle(
                info_x + 5, hand_bg_y - 8,
                info_x + bg_width - 15, hand_bg_y + 12,
                fill="#2a1a1a", outline="#4a2a2a", width=1
            )
            
            self.table_canvas.create_text(
                info_x + 10, hand_bg_y + 2, text=hand_text,
                fill="#ff9999", font=("Arial", 10), anchor=tk.W
            )
    
    def draw_community_cards(self, center_x, center_y):
        """Dibuja los cuadrados clicables para las cartas comunitarias (siempre 5)"""
        card_width = 50
        card_height = 70
        spacing = 12
        
        # Siempre mostrar 5 cuadrados
        max_cards = 5
        
        total_width = max_cards * card_width + (max_cards - 1) * spacing
        start_x = center_x - total_width // 2
        
        for idx in range(max_cards):
            card_x = start_x + idx * (card_width + spacing) + card_width // 2
            
            # Calcular coordenadas del rectángulo
            rect_x1 = card_x - card_width // 2
            rect_y1 = center_y - card_height // 2
            rect_x2 = card_x + card_width // 2
            rect_y2 = center_y + card_height // 2
            
            # Si hay carta en esta posición, mostrarla
            if idx < len(self.community_cards):
                card = self.community_cards[idx]
                self.draw_card(self.table_canvas, card_x, center_y, card, card_width, card_height, f"community_card_{idx}")
            else:
                # Dibujar carta boca abajo (diseño de carta oculta)
                # Sombra
                shadow_offset = 3
                self.table_canvas.create_rectangle(
                    rect_x1 + shadow_offset, rect_y1 + shadow_offset,
                    rect_x2 + shadow_offset, rect_y2 + shadow_offset,
                    fill="#000000", outline="", width=0, tags=f"community_card_{idx}"
                )
                
                # Carta boca abajo (azul oscuro con patrón)
                self.table_canvas.create_rectangle(
                    rect_x1, rect_y1, rect_x2, rect_y2,
                    fill="#1a237e", outline="#3f51b5", width=2,
                    tags=f"community_card_{idx}"
                )
                
                # Patrón decorativo
                pattern_color = "#283593"
                for i in range(3):
                    for j in range(4):
                        self.table_canvas.create_oval(
                            rect_x1 + 8 + i * 12, rect_y1 + 8 + j * 15,
                            rect_x1 + 12 + i * 12, rect_y1 + 12 + j * 15,
                            fill=pattern_color, outline="", width=0,
                            tags=f"community_card_{idx}"
                        )
            
            # Crear un rectángulo invisible más grande para hacer toda el área clicable
            self.table_canvas.create_rectangle(
                rect_x1 - 2, rect_y1 - 2, rect_x2 + 2, rect_y2 + 2,
                fill="", outline="", width=0,
                tags=f"community_card_{idx}_clickable"
            )
            
            # Hacer TODO clicable (tanto el rectángulo visible como el invisible)
            self.table_canvas.tag_bind(f"community_card_{idx}", "<Button-1>", 
                                     lambda e, idx=idx: self.open_card_selector("community", idx))
            self.table_canvas.tag_bind(f"community_card_{idx}", "<Button-3>", 
                                     lambda e, idx=idx: self.remove_community_card(idx))
            self.table_canvas.tag_bind(f"community_card_{idx}_clickable", "<Button-1>", 
                                     lambda e, idx=idx: self.open_card_selector("community", idx))
            self.table_canvas.tag_bind(f"community_card_{idx}_clickable", "<Button-3>", 
                                     lambda e, idx=idx: self.remove_community_card(idx))
    
    def set_dealer(self, player_id):
        """Establece el dealer haciendo clic en un jugador"""
        if player_id >= self.num_players:
            return
        
        self.dealer_position = player_id
        if hasattr(self, 'dealer_var'):
            self.dealer_var.set(str(player_id))
        
        # Redibujar para mostrar el nuevo dealer
        self.draw_table()
    
    def set_player_action(self, player_id, action):
        """Establece la acción de un jugador"""
        if player_id >= self.num_players:
            return
        
        # El jugador 0 (tú) no puede tener acciones marcadas
        if player_id == 0:
            return
        
        was_fold = False
        if action is None:
            # Quitar acción
            previous_action = self.player_actions.get(player_id)
            was_fold = (previous_action == 'fold')
            self.player_actions.pop(player_id, None)
            # Si era fold, removerlo de folded_players
            self.folded_players.discard(player_id)
        else:
            # Establecer acción
            self.player_actions[player_id] = action
            # Si es fold, añadirlo a folded_players
            if action == 'fold':
                self.folded_players.add(player_id)
            else:
                self.folded_players.discard(player_id)
        
        # Actualizar número de jugadores activos
        # Asegurar que el jugador 0 (tú) nunca esté en folded_players
        self.folded_players.discard(0)
        self.active_players = self.num_players - len(self.folded_players)
        
        # Actualizar acciones previas para recomendación
        self.update_previous_actions_from_players()
        
        # Redibujar la mesa
        self.draw_table()
        
        # Recalcular probabilidad si hay suficientes datos
        if len(self.my_cards) == 2:
            # Si se quitó un fold (action is None y era fold), recalcular inmediatamente
            if action is None and was_fold:
                # Cancelar cualquier timer pendiente
                if self.fold_delay_timer is not None:
                    self.root.after_cancel(self.fold_delay_timer)
                    self.fold_delay_timer = None
                self.update_probability()
            # Si es fold, esperar 3 segundos antes de recalcular (para permitir marcar múltiples rápidamente)
            elif action == 'fold':
                # Cancelar timer anterior si existe
                if self.fold_delay_timer is not None:
                    self.root.after_cancel(self.fold_delay_timer)
                    self.fold_delay_timer = None
                
                # Programar nuevo cálculo después de 3 segundos
                self.fold_delay_timer = self.root.after(3000, self._delayed_probability_update)
            else:
                # Para otras acciones (raise, call, etc.), recalcular inmediatamente
                # Cancelar cualquier timer pendiente de fold
                if self.fold_delay_timer is not None:
                    self.root.after_cancel(self.fold_delay_timer)
                    self.fold_delay_timer = None
                self.update_probability()
    
    def _delayed_probability_update(self):
        """Actualiza la probabilidad después del delay de 3 segundos"""
        self.fold_delay_timer = None
        if len(self.my_cards) == 2:
            self.update_probability()
    
    def update_previous_actions_from_players(self):
        """Actualiza las acciones previas basándose en las acciones de los jugadores"""
        has_raise = False
        num_raises = 0
        has_call = False
        
        # Revisar acciones de jugadores antes de ti (según posición)
        # Orden: después del dealer, antes de tu posición
        dealer_pos = self.dealer_position
        my_pos = self.my_position
        
        # Calcular el orden de acción (después del dealer)
        for i in range(self.num_players):
            player_id = (dealer_pos + 1 + i) % self.num_players
            if player_id == my_pos:
                break  # No considerar acciones después de ti
            
            action = self.player_actions.get(player_id, None)
            if action == 'raise' or action == '3bet' or action == 'all-in':
                has_raise = True
                num_raises += 1
                # 3bet y all-in cuentan como raises adicionales
                if action == '3bet':
                    num_raises += 1  # 3bet es un raise adicional
                elif action == 'all-in':
                    num_raises += 2  # All-in cuenta como múltiples raises
            elif action == 'call':
                has_call = True
        
        self.previous_actions = {
            'has_raise': has_raise,
            'has_call': has_call,
            'num_raises': num_raises
        }
    
    def update_table_players(self, event=None):
        """Actualiza el número de jugadores en la mesa"""
        try:
            new_num_players = int(self.players_var.get())
            if new_num_players != self.num_players:
                self.num_players = new_num_players
                # Limpiar jugadores retirados que ya no existen
                self.folded_players = {p for p in self.folded_players if p < self.num_players}
                self.active_players = self.num_players - len(self.folded_players)
                # Asegurar que la posición sea válida
                if self.my_position >= self.num_players:
                    self.my_position = 0
                    if hasattr(self, 'position_var'):
                        self.position_var.set("0")
                # Redibujar la mesa para mostrar los nuevos jugadores
                self.draw_table()
                # Recalcular probabilidad si hay suficientes datos
                if len(self.my_cards) == 2:
                    self.update_probability()
        except (ValueError, AttributeError, tk.TclError):
            # Si hay algún error, usar valor por defecto
            self.num_players = 2
            if hasattr(self, 'players_var'):
                self.players_var.set("2")
            self.draw_table()
    
    def update_my_position(self, event=None):
        """Actualiza la posición del jugador en la mesa"""
        try:
            self.my_position = int(self.position_var.get())
            if self.my_position >= self.num_players:
                self.my_position = 0
                self.position_var.set("0")
            # Actualizar acciones previas y redibujar
            self.update_previous_actions_from_players()
            self.draw_table()
        except (ValueError, AttributeError, tk.TclError):
            self.my_position = 0
            if hasattr(self, 'position_var'):
                self.position_var.set("0")
            self.draw_table()
    
    def update_dealer_position(self, event=None):
        """Actualiza la posición del dealer desde el combobox"""
        try:
            self.dealer_position = int(self.dealer_var.get())
            if self.dealer_position >= self.num_players:
                self.dealer_position = 0
                self.dealer_var.set("0")
            # Actualizar acciones previas y redibujar
            self.update_previous_actions_from_players()
            self.draw_table()
        except (ValueError, AttributeError, tk.TclError):
            self.dealer_position = 0
            if hasattr(self, 'dealer_var'):
                self.dealer_var.set("0")
            self.draw_table()
    
    def update_my_position(self, event=None):
        """Actualiza la posición del jugador en la mesa"""
        try:
            self.my_position = int(self.position_var.get())
            if self.my_position >= self.num_players:
                self.my_position = 0
                self.position_var.set("0")
            # Actualizar acciones previas y redibujar
            self.update_previous_actions_from_players()
            self.draw_table()
        except (ValueError, AttributeError, tk.TclError):
            self.my_position = 0
            if hasattr(self, 'position_var'):
                self.position_var.set("0")
            self.draw_table()
    
    def create_card_selector(self, parent, card_type, ranks, suits):
        """Crea un selector visual de cartas organizado por palos"""
        # Crear un frame para cada palo
        row = 0
        for suit_symbol, suit_name in suits.items():
            # Frame para este palo
            suit_frame = ttk.LabelFrame(parent, text=suit_name, padding="5")
            suit_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5, padx=5)
            
            # Crear botones para cada rango
            col = 0
            for rank in ranks:
                # Crear el texto de la carta
                card_text = f"{rank}{suit_symbol}"
                # Normalizar para el formato interno (10 -> T si es necesario)
                normalized_rank = rank if rank != '10' else '10'
                card_key = normalized_rank + suit_symbol
                
                # Determinar el color del texto (rojo para corazones y diamantes)
                text_color = "red" if suit_symbol in ['♥', '♦'] else "black"
                
                # Crear botón con color apropiado
                btn = tk.Button(suit_frame, text=card_text, width=4, height=2,
                               font=("Arial", 10, "bold"),
                               fg=text_color,
                               command=lambda c=card_key, ct=card_type: self.toggle_card(c, ct))
                
                btn.grid(row=0, column=col, padx=2, pady=2)
                
                # Guardar referencia al botón
                if card_type == "my":
                    self.my_card_buttons[card_key] = btn
                else:
                    self.community_card_buttons[card_key] = btn
                
                col += 1
            
            row += 1
    
    def update_community_buttons_state(self):
        """Actualiza el estado de los botones de cartas comunitarias según lo que esté revelado"""
        # Este método ya no es necesario con la nueva interfaz, pero se mantiene por compatibilidad
        pass
    
    def clear_all(self):
        """Limpia todas las cartas y reinicia"""
        self.my_cards = []
        self.community_cards = []
        self.folded_players = set()
        self.active_players = self.num_players
        self.current_probability = None
        self.current_top_losing_hands = []
        self.previous_actions = {
            'has_raise': False,
            'has_call': False,
            'num_raises': 0
        }
        self.draw_table()
    
    def normalize_card_format(self, card):
        """Convierte '10' a 'T' para compatibilidad con el evaluador"""
        if card.startswith('10'):
            return 'T' + card[2:]
        return card
    
    def get_card_key_from_normalized(self, normalized_card):
        """Obtiene la clave del botón desde una carta normalizada"""
        # Si tiene 'T', buscar la clave con '10'
        if normalized_card.startswith('T'):
            return '10' + normalized_card[1:]
        return normalized_card
    
    def toggle_card(self, card, card_type):
        """Alterna la selección de una carta"""
        # Normalizar formato (10 -> T)
        normalized_card = self.normalize_card_format(card)
        
        if card_type == "my":
            if normalized_card in self.my_cards:
                # Deseleccionar
                self.my_cards.remove(normalized_card)
                # Buscar el botón correcto (puede ser con '10' o 'T')
                btn_key = self.get_card_key_from_normalized(normalized_card)
                text_color = "red" if card[1] in ['♥', '♦'] else "black"
                if btn_key in self.my_card_buttons:
                    self.my_card_buttons[btn_key].config(relief=tk.RAISED, bg="SystemButtonFace", fg=text_color)
                elif card in self.my_card_buttons:
                    self.my_card_buttons[card].config(relief=tk.RAISED, bg="SystemButtonFace", fg=text_color)
            else:
                # Verificar que no esté ya seleccionada en comunitarias
                if normalized_card in self.community_cards:
                    messagebox.showwarning("Carta en uso", 
                                         "Esta carta ya está seleccionada como comunitaria.\nDeselecciónala primero.")
                    return
                
                # Seleccionar (máximo 2)
                if len(self.my_cards) >= 2:
                    messagebox.showwarning("Límite alcanzado", 
                                         "Solo puedes seleccionar 2 cartas propias.\nDeselecciona una primero.")
                    return
                self.my_cards.append(normalized_card)
                self.my_card_buttons[card].config(relief=tk.SUNKEN, bg="lightblue")
            
            self.my_cards_selected_label.config(text=f"Seleccionadas: {len(self.my_cards)}/2")
            
        else:  # community
            # Verificar que las cartas comunitarias estén reveladas
            max_allowed = 0
            if self.community_revealed['river']:
                max_allowed = 5
            elif self.community_revealed['turn']:
                max_allowed = 4
            elif self.community_revealed['flop']:
                max_allowed = 3
            else:
                messagebox.showwarning("Cartas no reveladas", 
                                     "Primero debes revelar las cartas comunitarias usando los botones de arriba.")
                return
            
            if normalized_card in self.community_cards:
                # Deseleccionar
                self.community_cards.remove(normalized_card)
                # Buscar el botón correcto
                btn_key = self.get_card_key_from_normalized(normalized_card)
                text_color = "red" if card[1] in ['♥', '♦'] else "black"
                if btn_key in self.community_card_buttons:
                    self.community_card_buttons[btn_key].config(relief=tk.RAISED, bg="SystemButtonFace", fg=text_color)
                elif card in self.community_card_buttons:
                    self.community_card_buttons[card].config(relief=tk.RAISED, bg="SystemButtonFace", fg=text_color)
            else:
                # Verificar que no esté ya seleccionada en mis cartas
                if normalized_card in self.my_cards:
                    messagebox.showwarning("Carta en uso", 
                                         "Esta carta ya está seleccionada como tuya.\nDeselecciónala primero.")
                    return
                
                # Seleccionar (según lo revelado)
                if len(self.community_cards) >= max_allowed:
                    messagebox.showwarning("Límite alcanzado", 
                                         f"Solo puedes seleccionar {max_allowed} cartas comunitarias según lo revelado.\nDeselecciona una primero.")
                    return
                self.community_cards.append(normalized_card)
                # Mantener el color del texto al seleccionar
                text_color = "red" if card[1] in ['♥', '♦'] else "black"
                self.community_card_buttons[card].config(relief=tk.SUNKEN, bg="lightgreen", fg=text_color)
            
            # Actualizar etiqueta de reveladas
            current = len(self.community_cards)
            if self.community_revealed['river']:
                self.community_selected_label.config(text=f"Reveladas: {current}/5 (River)", foreground="green")
            elif self.community_revealed['turn']:
                self.community_selected_label.config(text=f"Reveladas: {current}/4 (Turn)", foreground="green")
            elif self.community_revealed['flop']:
                self.community_selected_label.config(text=f"Reveladas: {current}/3 (Flop)", foreground="green")
        
        # Actualizar estado de botones comunitarios si es necesario
        if card_type == "community":
            self.update_community_buttons_state()
        
        # Habilitar botón de revelar flop cuando tengas 2 cartas
        if card_type == "my":
            if len(self.my_cards) == 2:
                self.reveal_flop_btn.config(state=tk.NORMAL)
            else:
                self.reveal_flop_btn.config(state=tk.DISABLED)
        
        # Actualizar probabilidad automáticamente si hay suficientes cartas
        if len(self.my_cards) == 2:
            self.update_probability()
        
        # Redibujar mesa para mostrar cartas actualizadas
        self.draw_table()
        
        # Redibujar mesa para mostrar cartas actualizadas
        if card_type == "my":
            self.draw_table()
    
    def normalize_card(self, card: str) -> Optional[str]:
        """Normaliza el formato de una carta"""
        card = card.strip()
        if not card:
            return None
        
        # Mapeo de palos
        suit_map = {
            's': '♠', 'S': '♠', '♠': '♠',
            'h': '♥', 'H': '♥', '♥': '♥',
            'd': '♦', 'D': '♦', '♦': '♦',
            'c': '♣', 'C': '♣', '♣': '♣'
        }
        
        # Mapeo de rangos
        rank_map = {
            'A': 'A', 'a': 'A',
            'K': 'K', 'k': 'K',
            'Q': 'Q', 'q': 'Q',
            'J': 'J', 'j': 'J',
            'T': 'T', 't': 'T', '10': '10'
        }
        
        # Extraer rango y palo
        if len(card) >= 2:
            # Formato: Rango + Palo (ej: As, Kh, 7d)
            rank = card[:-1].upper()
            suit_char = card[-1]
            
            # Normalizar rango
            if rank in rank_map:
                rank = rank_map[rank]
            elif rank.isdigit() and 2 <= int(rank) <= 9:
                rank = rank
            elif rank == '10':
                rank = '10'
            else:
                return None
            
            # Normalizar palo
            if suit_char in suit_map:
                suit = suit_map[suit_char]
            else:
                return None
            
            return rank + suit
        
        return None
    
    def clear_community(self):
        """Limpia las cartas comunitarias"""
        # Deseleccionar visualmente todos los botones
        for normalized_card in list(self.community_cards):
            btn_key = self.get_card_key_from_normalized(normalized_card)
            if btn_key in self.community_card_buttons:
                # Restaurar color original
                text_color = "red" if btn_key[1] in ['♥', '♦'] else "black"
                self.community_card_buttons[btn_key].config(relief=tk.RAISED, bg="SystemButtonFace", fg=text_color)
        
        self.community_cards = []
        self.community_selected_label.config(text="Seleccionadas: 0/5")
        self.update_probability()
    
    def clear_all(self):
        """Limpia todas las cartas y reinicia"""
        self.my_cards = []
        self.community_cards = []
        self.folded_players = set()
        self.active_players = self.num_players
        self.player_actions = {}
        self.previous_actions = {
            'has_raise': False,
            'has_call': False,
            'num_raises': 0
        }
        
        # Limpiar datos de probabilidad
        self.current_probability = None
        self.current_top_losing_hands = []
        
        self.draw_table()
    
    def update_probability(self):
        """Actualiza la probabilidad automáticamente"""
        # Calcular si tenemos 2 cartas propias (con o sin comunitarias)
        if len(self.my_cards) == 2:
            self.calculate_and_display()
        else:
            # Limpiar probabilidad si no hay suficientes cartas
            self.current_probability = None
            self.current_top_losing_hands = []
            self.draw_table()
    
    def calculate_and_display(self):
        """Calcula y muestra la probabilidad en un thread separado"""
        if len(self.my_cards) < 2:
            self.current_probability = None
            self.current_top_losing_hands = []
            self.draw_table()
            return
        
        # Cancelar cálculo anterior si existe
        self.calculation_in_progress = False
        if self.calculation_thread and self.calculation_thread.is_alive():
            # Esperar un momento para que termine el thread anterior
            pass
        
        # Mostrar indicador de cálculo
        self.current_probability = None
        self.current_top_losing_hands = []
        self.draw_table()  # Mostrar estado "calculando..."
        
        # Iniciar cálculo en thread separado
        self.calculation_in_progress = True
        self.calculation_thread = threading.Thread(
            target=self._calculate_probability_thread,
            daemon=True
        )
        self.calculation_thread.start()
    
    def _calculate_probability_thread(self):
        """Ejecuta el cálculo en un thread separado"""
        # Capturar valores actuales
        my_cards = self.my_cards.copy()
        community_cards = self.community_cards.copy()
        try:
            self.num_players = int(self.players_var.get())
        except (ValueError, AttributeError):
            self.num_players = 2
        
        # Normalizar cartas (asegurar formato correcto)
        my_cards = [self.normalize_card_format(c) for c in my_cards]
        community_cards = [self.normalize_card_format(c) for c in community_cards]
        
        # Usar jugadores activos (los que no se han retirado)
        # Asegurar que el jugador 0 (tú) siempre se cuenta
        self.folded_players.discard(0)
        active_players = self.active_players
        
        # Verificar que active_players sea válido (mínimo 1, que eres tú)
        if active_players < 1:
            active_players = 1
        
        # Calcular probabilidad usando solo jugadores activos
        # El cálculo ya cuenta correctamente: num_players incluye a todos (tú + oponentes)
        # Por ejemplo, si hay 8 jugadores totales y 2 se retiran, active_players = 6
        # El cálculo simulará 5 oponentes (6 totales - 1 que eres tú)
        probability, top_losing_hands = self.calculator.calculate_win_probability(
            my_cards,
            community_cards,
            active_players,  # Usar jugadores activos, no totales
            simulations=20000
        )
        
        # Verificar que el cálculo no fue cancelado
        if not self.calculation_in_progress:
            return
        
        # Actualizar en el thread principal de tkinter
        self.root.after(0, self._update_probability_result, probability, top_losing_hands)
    
    def _update_probability_result(self, probability, top_losing_hands):
        """Actualiza el resultado en el thread principal"""
        # Verificar que las cartas no hayan cambiado
        if len(self.my_cards) < 2:
            return
        
        # Guardar datos para mostrar en la mesa
        self.current_probability = probability
        self.current_top_losing_hands = top_losing_hands
        
        # Redibujar la mesa para mostrar la probabilidad y las manos
        self.draw_table()


def main():
    root = tk.Tk()
    app = PokerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
