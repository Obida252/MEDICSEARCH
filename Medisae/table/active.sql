PGDMP  '    $                 }            medications_db    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            	           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            
           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16586    active_ingredient    TABLE     u   CREATE TABLE public.active_ingredient (
    ain_id integer NOT NULL,
    ain_name character varying(255) NOT NULL
);
 %   DROP TABLE public.active_ingredient;
       public         heap r       postgres    false            �            1259    16585    active_ingredient_ain_id_seq    SEQUENCE     �   CREATE SEQUENCE public.active_ingredient_ain_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 3   DROP SEQUENCE public.active_ingredient_ain_id_seq;
       public               postgres    false    228                       0    0    active_ingredient_ain_id_seq    SEQUENCE OWNED BY     ]   ALTER SEQUENCE public.active_ingredient_ain_id_seq OWNED BY public.active_ingredient.ain_id;
          public               postgres    false    227            n           2604    16589    active_ingredient ain_id    DEFAULT     �   ALTER TABLE ONLY public.active_ingredient ALTER COLUMN ain_id SET DEFAULT nextval('public.active_ingredient_ain_id_seq'::regclass);
 G   ALTER TABLE public.active_ingredient ALTER COLUMN ain_id DROP DEFAULT;
       public               postgres    false    227    228    228                      0    16586    active_ingredient 
   TABLE DATA           =   COPY public.active_ingredient (ain_id, ain_name) FROM stdin;
    public               postgres    false    228   F                  0    0    active_ingredient_ain_id_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.active_ingredient_ain_id_seq', 147, true);
          public               postgres    false    227            p           2606    16593 0   active_ingredient active_ingredient_ain_name_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.active_ingredient
    ADD CONSTRAINT active_ingredient_ain_name_key UNIQUE (ain_name);
 Z   ALTER TABLE ONLY public.active_ingredient DROP CONSTRAINT active_ingredient_ain_name_key;
       public                 postgres    false    228            r           2606    16591 (   active_ingredient active_ingredient_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.active_ingredient
    ADD CONSTRAINT active_ingredient_pkey PRIMARY KEY (ain_id);
 R   ALTER TABLE ONLY public.active_ingredient DROP CONSTRAINT active_ingredient_pkey;
       public                 postgres    false    228               �  x�uV˖�8]�_Q��E1o��7
8�OL�I��seE�3�
��ҕM��/>�v0*%n9��dTFs��;�TNW����CkTA#n��=X%]�̣fQ�����u�TM�m����[�З���4J��f��ww�5��sR��N�����"/��"��|t����٥��YV���t!yܞn���v�R��mmUu�S��>��^�z��>>ۛ������/��(����u-��J5EB����k�2�jK��ͷ5�����g+R@D2�`;���x"Yr�yx�**8��XE���� ��(��z�I�^�LSk�i�ÞU��<[�y�ɲcǒ�/�p�We9I�Ͱ�@eš��.�YI<l��*���2��8�0��YC�ܫ���1�\�����"��3z˳����T��I���Y�Ū��yI�v��V�����gv[Vy���N�S��9@��4�`�n��]��GDH�m�@C��Ÿe2C4�o��o�:���ߦ�(����C[��;�d�m���O���$D_���lbn%�C��*����R���:P�t�*��&x����Z�"ʬ�q�D;fn���&�ZFu���_��J�DM�����������8�2�̃#���	FQ������(Sқ_�ÌF|	�^;D�j���DH��΂�s:�p�Gp�)��!���:'����ҫ� R��u��@?8w̩�+�K�n�S5� ����oCW4�O������j�<���;�}p�`H���_5�L��FN=�W�a�)�L��n������։g�jjr�I�elT����'4��
��A���/��(�S�߂���)[��lPh���2+LD�/a#P@w�U�񚱁W5!���&��m��M�^�	���Ń��[�{G�jp��}�Y��0��?V�\�ķ|A�r1�]t�e�g%�}a�j\vw8��n����I��p7�GTV(M��pPr?{��p��J�����cKZh�(P>���2k���x��v�Ơ�x���|+� �&.Z��L�0���b�qh܆jɏ	�r)pr�f)�j~d�ܡ���P�6JՈ�YШq:�F�$_[WqL�BI���Y���(:z�_���p\�����U�
2og�n!9���ٍ���K�8*�QJ�1�     