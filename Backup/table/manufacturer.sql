PGDMP      $                 }            medications_db    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            	           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            
           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16595    manufacturer    TABLE     i   CREATE TABLE public.manufacturer (
    manu_id integer NOT NULL,
    manu_name character varying(255)
);
     DROP TABLE public.manufacturer;
       public         heap r       postgres    false            �            1259    16594    manufacturer_manu_id_seq    SEQUENCE     �   CREATE SEQUENCE public.manufacturer_manu_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.manufacturer_manu_id_seq;
       public               postgres    false    230                       0    0    manufacturer_manu_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.manufacturer_manu_id_seq OWNED BY public.manufacturer.manu_id;
          public               postgres    false    229            n           2604    16598    manufacturer manu_id    DEFAULT     |   ALTER TABLE ONLY public.manufacturer ALTER COLUMN manu_id SET DEFAULT nextval('public.manufacturer_manu_id_seq'::regclass);
 C   ALTER TABLE public.manufacturer ALTER COLUMN manu_id DROP DEFAULT;
       public               postgres    false    229    230    230                      0    16595    manufacturer 
   TABLE DATA           :   COPY public.manufacturer (manu_id, manu_name) FROM stdin;
    public               postgres    false    230   �                  0    0    manufacturer_manu_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.manufacturer_manu_id_seq', 155, true);
          public               postgres    false    229            p           2606    16602 '   manufacturer manufacturer_manu_name_key 
   CONSTRAINT     g   ALTER TABLE ONLY public.manufacturer
    ADD CONSTRAINT manufacturer_manu_name_key UNIQUE (manu_name);
 Q   ALTER TABLE ONLY public.manufacturer DROP CONSTRAINT manufacturer_manu_name_key;
       public                 postgres    false    230            r           2606    16600    manufacturer manufacturer_pkey 
   CONSTRAINT     a   ALTER TABLE ONLY public.manufacturer
    ADD CONSTRAINT manufacturer_pkey PRIMARY KEY (manu_id);
 H   ALTER TABLE ONLY public.manufacturer DROP CONSTRAINT manufacturer_pkey;
       public                 postgres    false    230               �  x�}V[��6��N�l��]�c@�8m010ٙs��Xʼ���Οm�T�J*+��Ť��}R"j���R��wK�k���G�L��w�go&*�y�Ն�3�k��;�<x ��.|7SGJ	�5�T,>y�n�Dx��ڽ�ʀ#�r�N/Ҏ�
1-0W���m���D��G�cٸabc)V���>�X40�x�f����4>$B��ĩh�߰ΎpG���(r23��zi�@q)�pW�wK�����ݝ~'^Z�cǭ7S�a�%�ٚ���!������DI"F=�����$0ݚ��$O]Jr���g�����<0%���:�`��g�;+y�?�Mՙ�CH㗛�P"�f�4ݼ��x�4��󺕋��B!�~wf2�)-�bY=M&�BmCY�&�nt��,�~g��Sá����,��A3�q���烪��x؃��I��Š�TKp>+E�q�z��:" �<�"}��-W{�8FŚ����� ��2OE��lY>��D�]�a�M��!�i:뼫y���ěF=
�x�L�9��~[Ay!x���S(���BM�Lyy�lck^m��������Y�+��;������T$��m���O�L�E�J�HE~��C�+�[�e����LE�)����U�2Z�<Ryafآ��A�@^��LE}���e&znMHm	"ܩ|AY�UY��m�~�����T�K��z�&:��R�C�f�n�x<�a�q�ת~��hf�|IEt��U��*����*�?0�g�����Z^fB��������A+D�3U�	)�j��[`*�B w�̦�`�M:p�=���H��<�������U�9�1h\�*�f��e�%u� ڄ�\����^�c �¤�i�7��^u4teǚ�,UЙZky��x7�Ħǐ�����)�qt*��=�p�B�-oP���m]��KP�0�V����	��:*t�GA��G0w2�Ep�k��?����M�� �ۍ|O�)N����u�W�M]Ua� 9:%~���Kx��a��Z��r�s�o��q����v^~����jA�~���(Q�W�F�/S��Ճ%�W��9<+k� �/i�N�C*���4{���Vy<��$��U�0�0&���-W	S��˧��]������Y|=_'���^=��=]�B2���}S�?nD��YC     