PGDMP  *    "                 }            medications_db    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            	           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            
           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16561    pharmaceutic_form    TABLE     n   CREATE TABLE public.pharmaceutic_form (
    form_id integer NOT NULL,
    form_name character varying(255)
);
 %   DROP TABLE public.pharmaceutic_form;
       public         heap r       postgres    false            �            1259    16560    pharmaceutic_form_form_id_seq    SEQUENCE     �   CREATE SEQUENCE public.pharmaceutic_form_form_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 4   DROP SEQUENCE public.pharmaceutic_form_form_id_seq;
       public               postgres    false    224                       0    0    pharmaceutic_form_form_id_seq    SEQUENCE OWNED BY     _   ALTER SEQUENCE public.pharmaceutic_form_form_id_seq OWNED BY public.pharmaceutic_form.form_id;
          public               postgres    false    223            n           2604    16564    pharmaceutic_form form_id    DEFAULT     �   ALTER TABLE ONLY public.pharmaceutic_form ALTER COLUMN form_id SET DEFAULT nextval('public.pharmaceutic_form_form_id_seq'::regclass);
 H   ALTER TABLE public.pharmaceutic_form ALTER COLUMN form_id DROP DEFAULT;
       public               postgres    false    223    224    224                      0    16561    pharmaceutic_form 
   TABLE DATA           ?   COPY public.pharmaceutic_form (form_id, form_name) FROM stdin;
    public               postgres    false    224   P                  0    0    pharmaceutic_form_form_id_seq    SEQUENCE SET     K   SELECT pg_catalog.setval('public.pharmaceutic_form_form_id_seq', 7, true);
          public               postgres    false    223            p           2606    16568 1   pharmaceutic_form pharmaceutic_form_form_name_key 
   CONSTRAINT     q   ALTER TABLE ONLY public.pharmaceutic_form
    ADD CONSTRAINT pharmaceutic_form_form_name_key UNIQUE (form_name);
 [   ALTER TABLE ONLY public.pharmaceutic_form DROP CONSTRAINT pharmaceutic_form_form_name_key;
       public                 postgres    false    224            r           2606    16566 (   pharmaceutic_form pharmaceutic_form_pkey 
   CONSTRAINT     k   ALTER TABLE ONLY public.pharmaceutic_form
    ADD CONSTRAINT pharmaceutic_form_pkey PRIMARY KEY (form_id);
 R   ALTER TABLE ONLY public.pharmaceutic_form DROP CONSTRAINT pharmaceutic_form_pkey;
       public                 postgres    false    224               h   x�3�t�/�M-V�/J�I-�2��=�R�K�@��0������R��	BYFb��@Vj��_b1�S�l���ܚ��H.�s�hp��ə�9�� ��b���� 	�5�     