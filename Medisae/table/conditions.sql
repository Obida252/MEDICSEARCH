PGDMP      $                 }            medications_db    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            	           1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16437 
   conditions    TABLE     p   CREATE TABLE public.conditions (
    cond_id integer NOT NULL,
    cond_name character varying(255) NOT NULL
);
    DROP TABLE public.conditions;
       public         heap r       postgres    false            �            1259    16436    conditions_cond_id_seq    SEQUENCE     �   CREATE SEQUENCE public.conditions_cond_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.conditions_cond_id_seq;
       public               postgres    false    218            
           0    0    conditions_cond_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.conditions_cond_id_seq OWNED BY public.conditions.cond_id;
          public               postgres    false    217            n           2604    16440    conditions cond_id    DEFAULT     x   ALTER TABLE ONLY public.conditions ALTER COLUMN cond_id SET DEFAULT nextval('public.conditions_cond_id_seq'::regclass);
 A   ALTER TABLE public.conditions ALTER COLUMN cond_id DROP DEFAULT;
       public               postgres    false    217    218    218                      0    16437 
   conditions 
   TABLE DATA           8   COPY public.conditions (cond_id, cond_name) FROM stdin;
    public               postgres    false    218   /                  0    0    conditions_cond_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.conditions_cond_id_seq', 9, true);
          public               postgres    false    217            p           2606    16442    conditions conditions_pkey 
   CONSTRAINT     ]   ALTER TABLE ONLY public.conditions
    ADD CONSTRAINT conditions_pkey PRIMARY KEY (cond_id);
 D   ALTER TABLE ONLY public.conditions DROP CONSTRAINT conditions_pkey;
       public                 postgres    false    218               y   x����  г=��ݥ�-aɩ��Hݨ��b��靀$��k�g ����4Gq�U�W����ͭ'吤�Fq�;D�2�"�(�q(&T�	��ӒM��9�t�u�/�B�I����3/�     