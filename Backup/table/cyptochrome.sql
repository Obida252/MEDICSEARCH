PGDMP      *                 }            medications_db    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            	           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            
           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16460    cyptochrome    TABLE     o   CREATE TABLE public.cyptochrome (
    cyp_id integer NOT NULL,
    cyp_name character varying(255) NOT NULL
);
    DROP TABLE public.cyptochrome;
       public         heap r       postgres    false            �            1259    16459    cyptochrome_cyp_id_seq    SEQUENCE     �   CREATE SEQUENCE public.cyptochrome_cyp_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.cyptochrome_cyp_id_seq;
       public               postgres    false    222                       0    0    cyptochrome_cyp_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.cyptochrome_cyp_id_seq OWNED BY public.cyptochrome.cyp_id;
          public               postgres    false    221            n           2604    16463    cyptochrome cyp_id    DEFAULT     x   ALTER TABLE ONLY public.cyptochrome ALTER COLUMN cyp_id SET DEFAULT nextval('public.cyptochrome_cyp_id_seq'::regclass);
 A   ALTER TABLE public.cyptochrome ALTER COLUMN cyp_id DROP DEFAULT;
       public               postgres    false    222    221    222                      0    16460    cyptochrome 
   TABLE DATA           7   COPY public.cyptochrome (cyp_id, cyp_name) FROM stdin;
    public               postgres    false    222   �                  0    0    cyptochrome_cyp_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.cyptochrome_cyp_id_seq', 4927, true);
          public               postgres    false    221            p           2606    16467 $   cyptochrome cyptochrome_cyp_name_key 
   CONSTRAINT     c   ALTER TABLE ONLY public.cyptochrome
    ADD CONSTRAINT cyptochrome_cyp_name_key UNIQUE (cyp_name);
 N   ALTER TABLE ONLY public.cyptochrome DROP CONSTRAINT cyptochrome_cyp_name_key;
       public                 postgres    false    222            r           2606    16465    cyptochrome cyptochrome_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.cyptochrome
    ADD CONSTRAINT cyptochrome_pkey PRIMARY KEY (cyp_id);
 F   ALTER TABLE ONLY public.cyptochrome DROP CONSTRAINT cyptochrome_pkey;
       public                 postgres    false    222               s   x�-�;ADc�0� ˆ�jnj��?�3`���kޮ�{L�n�+�8��\p����Y���/B=i1�(�J ����.{)δz�rؿ#��2c�h��<�E�e��{�l�*/     